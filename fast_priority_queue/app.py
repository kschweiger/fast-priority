import asyncio
import logging
import os
from contextlib import asynccontextmanager
from time import sleep

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from redis import Redis
from rq import Queue
from rq.job import JobStatus

from fast_priority_queue.utils import generate_enpoint_list, run_request

load_dotenv()

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
# logger.setLevel(logging.DEBUG)

redis_conn = Redis(
    host=os.environ.get("FAST_PRIORITY_QUEUE_TARGET_REDIS_HOST", "localhost"),
    port=int(os.environ.get("FAST_PRIORITY_QUEUE_TARGET_REDIS_PORT", 6379)),
    username=os.environ.get("FAST_PRIORITY_QUEUE_TARGET_REDIS_USER", None),
    password=os.environ.get("FAST_PRIORITY_QUEUE_TARGET_REDIS_PASSWORD", None),
)
low_queue = Queue("low", connection=redis_conn)
high_queue = Queue("high", connection=redis_conn)

target_base_url = os.environ["FAST_PRIORITY_QUEUE_TARGET_BASE_URL"]
job_poll_interval = float(os.environ.get("FAST_PRIORITY_QUEUE_POLL_INTERVAL", 1.0))
job_ttl = int(os.environ.get("FAST_PRIORITY_QUEUE_TTL", 60 * 5))

low_prio_paths = None
low_prio_base_paths = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global low_prio_paths
    global low_prio_base_paths

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
            logger.info(f"Low priority path")
            for path in low_prio_paths:
                logger.info(f"    {path}")
        if low_prio_base_paths:
            logger.info(f"Low priority base path")
            for path in low_prio_base_paths:
                logger.info(f"    {path}")

    yield


app = FastAPI(
    lifespan=lifespan,
)


async def forward_request(request: Request, path: str):
    assert low_prio_paths is not None
    assert low_prio_base_paths is not None
    # Prepare request components
    url = f"/{path}?{request.url.query}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove original host header

    request_body = await request.body()

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
            f"Waiting. Current status: %s of %s", job.get_status(refresh=True), job.id
        )
        await asyncio.sleep(job_poll_interval)

    return job.result


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy_request(request: Request, path: str):
    try:
        response = await forward_request(request, path)
        return response.json()
    except httpx.ConnectError:
        return {"error": "Target server unavailable"}
