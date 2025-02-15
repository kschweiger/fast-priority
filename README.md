# 🚀 Fast Priority Queue 🔥

A minimal priority queuing gateway built with FastAPI using Redis.

It is designed to sit between your clients and a backend REST API, managing two priority levels—high and low—using the [`rq` package](https://python-rq.org/). Requests are enqueued based on the request path and processed synchronously by dedicated worker processes, so the overall throughput is limited by the number of workers.

## Overview

- Intercepts incoming client requests and forwards them to a target REST API.
- Enqueues requests into either a high-priority or low-priority queue based on configurable path matching.
- Processes queued requests via worker processes running in a separate environment.
- Offers Dockerized deployment for both the gateway and worker processes.


## Configuration ⚙️

Both the gateway and workers are fully configurable via the following environment variables.

### Gateway

| ENV                                       | Description                                                                                                                           | Required | Default   |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
| FAST_PRIORITY_QUEUE_TARGET_BASE_URL       | Base url of the target REST api which should run behind the gateway                                                                   | x        |           |
| FAST_PRIORITY_QUEUE_LOW_PRIO_PATHS        | Comma separated list of paths on the target API that should have low priority. Low priority for exact matches                         |          | None      |
| FAST_PRIORITY_QUEUE_LOW_PRIO_BASE_PATHS   | Comma separated list of paths on the target API that should have low priority. Low priority if a request paths starts with the value. |          | None      |
| FAST_PRIORITY_QUEUE_PASS_THROUGH          | Comma separated list of paths on the target API that should skip the queue. Request will be directly be passed on.                    |          | health/   |
| FAST_PRIORITY_QUEUE_POLL_INTERVAL         | How often should each request check if the job is finished                                                                            |          | 1.0       |
| FAST_PRIORITY_QUEUE_TTL                   | Time-to-live (in seconds) for jobs on the queues.	                                                                                    |          | 300       |
| FAST_PRIORITY_QUEUE_REDIS_HOST            | Redis host                                                                                                                            |          | localhost |
| FAST_PRIORITY_QUEUE_REDIS_PORT            | Redis port                                                                                                                            |          | 6379      |
| FAST_PRIORITY_QUEUE_REDIS_USER            | Redis username                                                                                                                        |          | None      |
| FAST_PRIORITY_QUEUE_REDIS_PASSWORD        | Redis password                                                                                                                        |          | None      |

### Queue worker (docker)

| ENV                                       | Description                                                                                                                           | Required | Default   |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
| FAST_PRIORITY_QUEUE_WORKER                | Set (e.g., non-empty or a number) to run as a worker instead of the gateway. Controls the number of worker processes to launch.       | x        |           |
| FAST_PRIORITY_QUEUE_REDIS_HOST            | Redis host                                                                                                                            |          | localhost |
| FAST_PRIORITY_QUEUE_REDIS_PORT            | Redis port                                                                                                                            |          | 6379      |
| FAST_PRIORITY_QUEUE_REDIS_USER            | Redis username                                                                                                                        |          | None      |
| FAST_PRIORITY_QUEUE_REDIS_PASSWORD        | Redis password                                                                                                                        |          | None      |

## Usage

Fast Priority Queue is designed to run via Docker (or Docker Compose), but you can also run the components individually during development. 

For example:

```bash
fastapi run fast_priority_queue/app.py --host 0.0.0.0 --port 8001
rq worker high low 
```

### Docker 🐳

You can build the Docker container using the provided Dockerfile. The container adapts its run mode based on the presence of the environment variable `FAST_PRIORITY_QUEUE_WORKER`:

- If `FAST_PRIORITY_QUEUE_WORKER` is set, the container starts the worker(s).
- If not, the gateway is started.



#### Examples 


```bash
# API
docker run -p 8010:8000 -e FAST_PRIORITY_QUEUE_TARGET_BASE_URL=http://localhost:8011 -e FAST_PRIORITY_QUEUE_REDIS_HOST=localhost fast_priority_queue:latest

# Workers
docker run -p 8010:8000 -e  FAST_PRIORITY_QUEUE_WORKER=1 -e FAST_PRIORITY_QUEUE_REDIS_HOST=localhost fast_priority_queue:latest
```


#### Compose 🐳🐳🐳

The simplest way to run Fast Priority Queue and its dependencies is via Docker Compose. Below is an example configuration:

```yml
services:
  behind_gateway_api:
    ...
  priorityity-gateway:
    image: fast_priority_queue:latest
    environment:
      - FAST_PRIORITY_QUEUE_TARGET_BASE_URL=http://behind_gateway_api:8000
      - FAST_PRIORITY_QUEUE_REDIS_HOST=queue
      - FAST_PRIORITY_QUEUE_LOW_PRIO_PATHS=endpoint_1,endpoint_2
    ports:
      - 8066:8000
      
  priority-gateway-worker:
    image: fast_priority_queue:latest
    environment:
      - FAST_PRIORITY_QUEUE_WORKERS=1
      - FAST_PRIORITY_QUEUE_REDIS_HOST=queue
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

