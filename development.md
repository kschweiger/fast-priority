# Development notes

## Run for hands on development and test

Start a plain redis container using docker

```bash
docker run --name some-redis -d redis
```

Create a `.env` file in the project root and defined (at least) the target url
```
FAST_PRIORITY_TARGET_BASE_URL="http://localhost:8010"
```

In different terminal sessions run

```bash
uv run fastapi dev examples/end2end/app.py --host 0.0.0.0 --port 8010
```

```bash
uv run fastapi dev fast_priority_queue/app.py --host 0.0.0.0 --port 8001
```

Now send curl requests to `localhost:8001` to test the gateway
