# End2End example using docker compose 

Before running docker-compose here, run the `make build` command from the project root to build the base image of the gateway

Then you can run
```bash
docker compose up
```

This will start containers, for the 

1. Priority gateway
2. workers for the gateway
3. Redis 
4. And a simple REST API defined in `app.py` which runs behind the gateway

From a different terminal session, you can send curl requests to the gateway at `localhost:8066` and watch the output.
