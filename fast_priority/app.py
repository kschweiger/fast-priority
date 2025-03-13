import asyncio
import logging
import os
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue
from rq.job import JobStatus

from fast_priority.utils import generate_enpoint_list, normalize_paths, run_request

load_dotenv()


class HighPrioPaths(StrEnum):
    LISTED = "listed"
    UNLISTED = "unlisted"


logger = logging.getLogger("uvicorn.error")
# logger.setLevel(logging.DEBUG)

redis_conn = Redis(
    host=os.environ.get("FAST_PRIORITY_REDIS_HOST", "localhost"),
    port=int(os.environ.get("FAST_PRIORITY_REDIS_PORT", 6379)),
    username=os.environ.get("FAST_PRIORITY_REDIS_USER", None),
    password=os.environ.get("FAST_PRIORITY_REDIS_PASSWORD", None),
)
low_queue = Queue("low", connection=redis_conn)
high_queue = Queue("high", connection=redis_conn)

target_base_url = os.environ["FAST_PRIORITY_TARGET_BASE_URL"]
priority_mode = HighPrioPaths(
    os.environ.get("FAST_PRIORITY_HIGH_PRIO_PATHS", "unlisted")
)
job_poll_interval = float(os.environ.get("FAST_PRIORITY_POLL_INTERVAL", 1.0))
job_ttl = int(os.environ.get("FAST_PRIORITY_TTL", 60 * 5))

doc_path = os.environ.get("FAST_PRIORITY_DOC_PATH", "/gateway_docs")
redoc_path = os.environ.get("FAST_PRIORITY_REDOC_PATH", "/gateway_redoc")
health_path = os.environ.get("FAST_PRIORITY_HEALTH_PATH", "/gateway_health")
normalize_urls = bool(os.environ.get("FAST_PRIORITY_NORMALIZE_PATHS", 1))

prio_paths = None
prio_base_paths = None
pass_through_paths = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global prio_paths
    global prio_base_paths
    global pass_through_paths

    pass_through_paths = ["health"]
    pass_through_env = os.environ.get("FAST_PRIORITY_PASS_THROUGH", None)
    if pass_through_env:
        pass_through_paths = generate_enpoint_list(pass_through_env)

    prio_paths = generate_enpoint_list(os.environ.get("FAST_PRIORITY_PRIO_PATHS", None))
    prio_base_paths = generate_enpoint_list(
        os.environ.get("FAST_PRIORITY_PRIO_BASE_PATHS", None)
    )

    if normalize_urls:
        logger.info("Path normalization enabled")
        pass_through_paths = normalize_paths(pass_through_paths)
        prio_paths = normalize_paths(prio_paths)
    if not prio_base_paths and not prio_paths:
        logger.warning("No low priority endpoints defined.")
    else:
        if priority_mode == HighPrioPaths.LISTED:
            logger.info("The following path will be passed to the **HIGH** queue")
        else:
            logger.info("The following path will be passed to the **LOW** queue")
        if prio_paths:
            logger.info("Low priority path")
            for path in prio_paths:
                logger.info(f"    {path}")
        if prio_base_paths:
            logger.info("Low priority base path")
            for path in prio_base_paths:
                logger.info(f"    {path}")

    if pass_through_paths:
        logger.info("Pass through paths")
        for path in pass_through_paths:
            logger.info(f"    {path}")
    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url=doc_path,
    redoc_url=redoc_path,
)


@app.get(health_path)
async def heath_check() -> Any:
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{target_base_url}")
    except httpx.ConnectError:
        target_reachable = False
    else:
        target_reachable = True

    try:
        redis_conn.info()
    except RedisConnectionError:
        redis_reachable = False
    else:
        redis_reachable = True

    n_jobs_queued_low = None
    n_jobs_queued_high = None
    if redis_reachable:
        n_jobs_queued_high = len(high_queue.jobs)
        n_jobs_queued_low = len(low_queue.jobs)

    return {
        "target_reachable": target_reachable,
        "redis_reachable": redis_reachable,
        "queue": {"high": n_jobs_queued_high, "low": n_jobs_queued_low},
    }


@app.get("/docs", include_in_schema=False)
@app.get("/redoc", include_in_schema=False)
async def get_target_docs(request: Request) -> Any:
    current_path = request.url.path
    async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
        response = await client.get(  # type: ignore
            url=f"{target_base_url}{current_path}",
        )
    new_content = response.content.decode("utf-8").replace(
        "/openapi.json", "/target_openapi.json"
    )
    new_bytes = new_content.encode("utf-8")
    new_headers = dict(response.headers)
    new_headers["content-length"] = str(len(new_bytes))
    return Response(
        content=new_bytes,
        status_code=response.status_code,
        headers=new_headers,
    )


@app.get("/target_openapi.json")
async def get_target_openapi_spec() -> Any:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{target_base_url}/openapi.json")
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


async def forward_request(request: Request, path: str) -> Response:
    assert prio_paths is not None
    assert prio_base_paths is not None
    # Prepare request components
    url = f"/{path}?{request.url.query}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove original host header

    request_body = await request.body()

    if pass_through_paths and path in pass_through_paths:
        logger.debug("%s in pass through. Skipping queue", path)
        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            return await client.request(  # type: ignore
                method=request.method,
                url=f"{target_base_url}{url}",
                headers=headers,
                content=request_body,
            )

    use_queue = high_queue if priority_mode == HighPrioPaths.UNLISTED else low_queue
    if path in prio_paths or any(path.startswith(b) for b in prio_base_paths):
        use_queue = low_queue if priority_mode == HighPrioPaths.UNLISTED else high_queue

    job = use_queue.enqueue(
        run_request,
        ttl=job_ttl,
        failure_ttl=60 * 60,
        kwargs=dict(
            method=request.method,
            url=f"{target_base_url}{url}",
            headers=headers,
            content=request_body,
        ),
    )

    while job.result is None:
        status = job.get_status(refresh=True)
        if status in [JobStatus.FAILED, JobStatus.STOPPED, JobStatus.CANCELED]:
            raise HTTPException(status_code=500, detail="Could not run request")
        logger.debug(
            "Waiting. Current status: %s of %s", job.get_status(refresh=True), job.id
        )
        await asyncio.sleep(job_poll_interval)

    return job.result


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"],
    include_in_schema=False,
)
async def proxy_request(request: Request, path: str) -> Any:
    response = await forward_request(request, path)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response.headers,
    )
