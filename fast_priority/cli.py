#!/usr/bin/env python3
import os
import sys
from urllib.parse import quote

import uvicorn


def urlencode(s: str) -> str:
    safe = "-_.~"
    return quote(s, safe=safe)


def main():
    role = "worker" if os.getenv("FAST_PRIORITY_WORKERS") else "api"

    print("======================================")
    print("==> Fast Priority Queue RUN SCRIPT <==")
    print("======================================")
    print(f"--> MODE: {role}")
    print("======================================")

    if role == "api":
        from fast_priority.app import app

        uvicorn.run(
            app,
            host=os.getenv("FAST_PRIORITY_HOST", "0.0.0.0"),
            port=int(os.getenv("FAST_PRIORITY_PORT", 8000)),
            # log_level="debug",
            reload=False,  # Disabled for production
        )
    elif role == "worker":
        from rq.cli.cli import main as rq_cli

        print("Running queue worker")
        workers = os.getenv("FAST_PRIORITY_WORKERS", "1")
        print(f"Using {workers} workers")

        redis_host = os.getenv("FAST_PRIORITY_REDIS_HOST", "localhost")
        redis_user = os.getenv("FAST_PRIORITY_REDIS_USER", "")
        redis_password = os.getenv("FAST_PRIORITY_REDIS_PASSWORD", "")
        redis_port = os.getenv("FAST_PRIORITY_REDIS_PORT", "")

        auth = ""
        if redis_user and redis_password:
            auth = f"{urlencode(redis_user)}:{urlencode(redis_password)}@"
        elif redis_password:
            auth = f":{urlencode(redis_password)}@"

        uri = f"redis://{auth}{redis_host}"
        if redis_port:
            uri += f":{redis_port}"

        print(f"  Using redis uri: {uri}")

        try:
            worker_count = int(workers)
            if worker_count < 1:
                raise ValueError
        except ValueError:
            print("ERR:: Invalid value for worker")
            sys.exit(1)

        if worker_count == 1:
            print("Running with one worker")
            rq_cli(["worker", "high", "low", "--url", uri], standalone_mode=True)

        else:
            print("Running multiple workers")
            rq_cli(
                [
                    "worker-pool",
                    "high",
                    "low",
                    "-n",
                    str(worker_count),
                    "--url",
                    uri,
                ],
                standalone_mode=True,
            )

    else:
        print("ERR:: Invalid run mode")
        sys.exit(1)


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    main()
