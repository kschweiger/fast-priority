import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue
from rq.job import JobStatus

from fast_priority_queue.utils import generate_enpoint_list, run_request

load_dotenv()

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
# logger.setLevel(logging.DEBUG)

redis_conn = Redis(
    host=os.environ.get("FAST_PRIORITY_QUEUE_REDIS_HOST", "localhost"),
    port=int(os.environ.get("FAST_PRIORITY_QUEUE_REDIS_PORT", 6379)),
    username=os.environ.get("FAST_PRIORITY_QUEUE_REDIS_USER", None),
    password=os.environ.get("FAST_PRIORITY_QUEUE_REDIS_PASSWORD", None),
)
low_queue = Queue("low", connection=redis_conn)
high_queue = Queue("high", connection=redis_conn)

target_base_url = os.environ["FAST_PRIORITY_QUEUE_TARGET_BASE_URL"]
job_poll_interval = float(os.environ.get("FAST_PRIORITY_QUEUE_POLL_INTERVAL", 1.0))
job_ttl = int(os.environ.get("FAST_PRIORITY_QUEUE_TTL", 60 * 5))

low_prio_paths = None
low_prio_base_paths = None
pass_through_paths = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global low_prio_paths
    global low_prio_base_paths
    global pass_through_paths

    pass_through_paths = ["health/"]
    pass_through_env = os.environ.get("FAST_PRIORITY_QUEUE_PASS_THROUGH", None)
    if pass_through_env:
        pass_through_paths = generate_enpoint_list(pass_through_env)

    low_prio_paths = generate_enpoint_list(
        os.environ.get("FAST_PRIORITY_QUEUE_LOW_PRIO_PATHS", None)
    )
    low_prio_base_paths = generate_enpoint_list(
        os.environ.get("FAST_PRIORITY_QUEUE_LOW_PRIO_BASE_PATHS", None)
    )

    if not low_prio_base_paths and not low_prio_paths:
        logger.warning("No low priority endpoints defined.")
    else:
        if low_prio_paths:
            logger.info("Low priority path")
            for path in low_prio_paths:
                logger.info(f"    {path}")
        if low_prio_base_paths:
            logger.info("Low priority base path")
            for path in low_prio_base_paths:
                logger.info(f"    {path}")

    if pass_through_paths:
        logger.info("Pass through paths")
        for path in pass_through_paths:
            logger.info(f"    {path}")
    yield


app = FastAPI(
    lifespan=lifespan,
)


@app.get("/gateway_health/")
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


async def forward_request(request: Request, path: str) -> Response:
    assert low_prio_paths is not None
    assert low_prio_base_paths is not None
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

    use_queue = high_queue
    if path in low_prio_paths or any(path.startswith(b) for b in low_prio_base_paths):
        use_queue = low_queue

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


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy_request(request: Request, path: str) -> Any:
    response = await forward_request(request, path)
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response.headers,
    )
