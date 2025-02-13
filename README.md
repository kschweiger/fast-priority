# 🚀 Fast Priority Queue 🔥

A minimal priority queuing gateway built with FastAPI using Redis

## Configuration ⚙️

| ENV                                       | Description                                                                                                                           | Required | Default   |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|----------|-----------|
| FAST_PRIORITY_QUEUE_TARGET_BASE_URL       | Base url of the target REST api which should run behind the gateway                                                                   | x        |           |
| FAST_PRIORITY_QUEUE_LOW_PRIO_PATHS        | Comma separated list of paths on the target API that should have low priority. Low priority for exact matches                         |          | None      |
| FAST_PRIORITY_QUEUE_LOW_PRIO_BASE_PATHS   | Comma separated list of paths on the target API that should have low priority. Low priority if a request paths starts with the value. |          | None      |
| FAST_PRIORITY_QUEUE_POLL_INTERVAL         | How often should each request check if the job is finished                                                                            |          | 1.0       |
| FAST_PRIORITY_QUEUE_TTL                   | TTL of jobs on the queues                                                                                                             |          | 300       |
| FAST_PRIORITY_QUEUE_TARGET_REDIS_HOST     | Redis host                                                                                                                            |          | localhost |
| FAST_PRIORITY_QUEUE_TARGET_REDIS_PORT     | Redis port                                                                                                                            |          | 6379      |
| FAST_PRIORITY_QUEUE_TARGET_REDIS_USER     | Redis username                                                                                                                        |          | None      |
| FAST_PRIORITY_QUEUE_TARGET_REDIS_PASSWORD | Redis password                                                                                                                        |          | None      |

## Docker 🐳

Build the container with the provided Dockerfile

Then run it with something like this:

```bash
docker run -p 8010:8000 -e FAST_PRIORITY_QUEUE_TARGET_BASE_URL=http://localhost:8011 -e FAST_PRIORITY_QUEUE_TARGET_REDIS_HOST=localhost fast_priority_queue:latest
```


### Compose 🐳🐳🐳

Idea is to use this inside some kind of docker compose configuartion. Here is a snippet:

```yml
services:
  behind_gateway_api:
    ...
  priorityity-gateway:
    image: fast_priority_queue:latest
    environment:
      - FAST_PRIORITY_QUEUE_TARGET_BASE_URL=http://behind_gateway_api:8000
      - FAST_PRIORITY_QUEUE_TARGET_REDIS_HOST=queue
      - FAST_PRIORITY_QUEUE_LOW_PRIO_PATHS=endpoint_1,endpoint_2
    ports:
      - 8066:8000
    networks:
      - default
  priority-gateway-worker:
    image: fast_priority_queue:latest
    environment:
      - FAST_PRIORITY_QUEUE_WORKERS=1
      - FAST_PRIORITY_QUEUE_TARGET_REDIS_HOST=queue
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
