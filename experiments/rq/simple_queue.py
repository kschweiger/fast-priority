import time

from func import run_get_request
from redis import Redis
from rq import Queue

# Tell RQ what Redis connection to use
redis_conn = Redis()
ql = Queue("low", connection=redis_conn)  # no args implies the default queue
qh = Queue("high", connection=redis_conn)  # no args implies the default queue

# Delay execution of count_words_at_url('http://nvie.com')
jobs = []
for param_1 in range(10):
    jobs.append(
        ql.enqueue(
            run_get_request,
            f"http://localhost:8010/endpoint_1/?param_1={param_1}&param_2=d",
        ),
    )
for req_url in [
    "http://localhost:8010/endpoint_1/?param_1=55&param_2=d",
    "http://localhost:8010/endpoint_1/?param_1=66&param_2=d",
    "http://localhost:8010/endpoint_1/?param_1=77&param_2=d",
]:
    jobs.append(
        qh.enqueue(run_get_request, req_url),
    )


while any(job.result is None for job in jobs):
    print(
        "Waiting.... Complete: %s / %s"
        % (sum(job.result is not None for job in jobs), len(jobs)),
    )
    time.sleep(1)
for job in jobs:
    print(job.result)  # => 889  # Changed to job.return_value() in RQ >= 1.12.0
