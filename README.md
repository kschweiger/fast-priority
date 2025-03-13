# 🚀 Fast Priority Queue 🔥

A minimal priority queuing gateway built with FastAPI using Redis.

It is designed to sit between your clients and a backend REST API, managing two priority levels—high and low—using the [`rq` package](https://python-rq.org/). Requests are enqueued based on the request path and processed synchronously by dedicated worker processes, so the overall throughput is limited by the number of workers.

## Overview

- Intercepts incoming client requests and forwards them to a target REST API.
- Enqueues requests into either a high-priority or low-priority queue based on configurable path matching.
- Processes queued requests via worker processes running in a separate environment.
- Pass through to `/docs` and `/redoc` endpoints with `openapi.json` definitions of target REST API
- Offers Dockerized deployment for both the gateway and worker processes.


## Configuration ⚙️

Both the gateway and workers are fully configurable via the following environment variables.

### Gateway

| ENV                                 | Description                                                                                                                                | Required | Default         |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|----------|-----------------|
| FAST_PRIORITY_TARGET_BASE_URL       | Base url of the target REST api which should run behind the gateway                                                                        | x        |                 |
| FAST_PRIORITY_HIGH_PRIO_PATHS       | Switch between **listed** and **unlisted** modes. If **listed** (**unlisted**) the paths defined in the _PATH_ env variables are put on the **high** (**low**) queue |          | unlisted        |
| FAST_PRIORITY_PRIO_PATHS            | Comma separated list of paths on the target API that should have low priority. Low priority for exact matches                              |          | None            |
| FAST_PRIORITY_PRIO_BASE_PATHS       | Comma separated list of paths on the target API that should have low priority. Low priority if a request paths starts with the value.      |          | None            |
| FAST_PRIORITY_PASS_THROUGH          | Comma separated list of paths on the target API that should skip the queue. Request will be directly be passed on.                         |          | health/         |
| FAST_PRIORITY_POLL_INTERVAL         | How often should each request check if the job is finished                                                                                 |          | 1.0             |
| FAST_PRIORITY_TTL                   | Time-to-live (in seconds) for jobs on the queues.	                                                                                         |          | 300             |
| FAST_PRIORITY_REDIS_HOST            | Redis host                                                                                                                                 |          | localhost       |
| FAST_PRIORITY_REDIS_PORT            | Redis port                                                                                                                                 |          | 6379            |
| FAST_PRIORITY_REDIS_USER            | Redis username                                                                                                                             |          | None            |
| FAST_PRIORITY_REDIS_PASSWORD        | Redis password                                                                                                                             |          | None            |
| FAST_PRIORITY_DOC_PATH              | Endpoint for the openapi /docs enpoint of the gateway                                                                                      |          | /gateway_docs   |
| FAST_PRIORITY_REDOC_PATH            | Endpoint for the openapi /redoc enpoint of the gateway                                                                                     |          | /gateway_redoc  |
| FAST_PRIORITY_HEALTH_PATH           | Endpoint for the healts check of the gateway                                                                                               |          | /gateway_health |
| FAST_PRIORITY_NORMALIZE_PATHS       | Set wheather paths defined in should be normalized regaring trailign /. Applyies to FAST_PRIORITY_PRIO_PATH and FAST_PRIORITY_PASS_THROUGH |          | 1               |

### Queue worker (docker)

| ENV                                 | Description                                                                                                                           | Required | Default   |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
| FAST_PRIORITY_WORKERS               | Set (e.g., non-empty or a number) to run as a worker instead of the gateway. Controls the number of worker processes to launch.       | x        |           |
| FAST_PRIORITY_REDIS_HOST            | Redis host                                                                                                                            |          | localhost |
| FAST_PRIORITY_REDIS_PORT            | Redis port                                                                                                                            |          | 6379      |
| FAST_PRIORITY_REDIS_USER            | Redis username                                                                                                                        |          | None      |
| FAST_PRIORITY_REDIS_PASSWORD        | Redis password                                                                                                                        |          | None      |

## Usage

Fast Priority Queue is designed to run via Docker (or Docker Compose) or using the script installed with the package `run-fast-priority`. The configuration works the same for both approaches using the environment variables described in [Configuration section](#configuration). The script is mainly provide to give the user the flexibility to include the gateway in their own docker containers by installing the package via pypi.

For development (or more specialized application) the gateway can also be run using the underlying command like this:

```bash
fastapi run fast_priority/app.py --host 0.0.0.0 --port 8001
rq worker high low
```

### Docker 🐳

You can build the Docker container using the provided Dockerfile. The container adapts its run mode based on the presence of the environment variable `FAST_PRIORITY_WORKER`:

- If `FAST_PRIORITY_WORKER` is set, the container starts the worker(s).
- If not, the gateway is started.

The same strategy can be used with you own container and installing the package in the Dockerfile from pypi.


#### Examples

```bash
# API
docker run -p 8010:8000 -e FAST_PRIORITY_TARGET_BASE_URL=http://localhost:8011 -e FAST_PRIORITY_REDIS_HOST=localhost fast_priority:latest

# Workers
docker run -p 8010:8000 -e  FAST_PRIORITY_WORKER=1 -e FAST_PRIORITY_REDIS_HOST=localhost fast_priority:latest
```


#### Compose 🐳🐳🐳

The simplest way to run Fast Priority Queue and its dependencies is via Docker Compose. Below is an example configuration:

```yml
services:
  behind_gateway_api:
    ...
  priorityity-gateway:
    image: fast_priority:latest
    environment:
      - FAST_PRIORITY_TARGET_BASE_URL=http://behind_gateway_api:8000
      - FAST_PRIORITY_REDIS_HOST=queue
      - FAST_PRIORITY_PRIO_PATHS=endpoint_1,endpoint_2
    ports:
      - 8066:8000

  priority-gateway-worker:
    image: fast_priority:latest
    environment:
      - FAST_PRIORITY_WORKERS=1
      - FAST_PRIORITY_REDIS_HOST=queue
    networks:
      - default
  queue:
    image: redis
    networks:
      - default

networks:
  default:
    driver: bridge

```


## Contributing
Contributions to Fast Priority Queue are welcome! Feel free to open issues or submit pull requests with improvements, bug fixes, or feature suggestions.

