# Testing RQ

Requires a REDIS instance on localhost

## simple_queue.py

Simple blocking test with two queues

Run the worker and start the test app
```bash
uv run fastapi dev tests/test_api/app.py --host 0.0.0.0 --port 8010
cd experiments/rq
uv run rq worker high default low  
```

and then run the script with:

```bash
uv run python simple_queue.py
```

When watching the fastapi output you should see that the high prio jobs (with `55`, `66` and `77` for `param_1`) as second, third and fourth requests even tough they are submitted after the job with `param_1=7`

```
      INFO   Application startup complete.
      INFO   127.0.0.1:61211 - "GET /endpoint_1/?param_1=1&param_2=a HTTP/1.1" 200
      INFO   127.0.0.1:61214 - "GET /endpoint_1/?param_1=55&param_2=d HTTP/1.1" 200
      INFO   127.0.0.1:61217 - "GET /endpoint_1/?param_1=66&param_2=d HTTP/1.1" 200
      INFO   127.0.0.1:61220 - "GET /endpoint_1/?param_1=76&param_2=d HTTP/1.1" 200
      INFO   127.0.0.1:61223 - "GET /endpoint_1/?param_1=2&param_2=b HTTP/1.1" 200
      INFO   127.0.0.1:61226 - "GET /endpoint_1/?param_1=3&param_2=c HTTP/1.1" 200
      INFO   127.0.0.1:61229 - "GET /endpoint_1/?param_1=4&param_2=d HTTP/1.1" 200
      INFO   127.0.0.1:61234 - "GET /endpoint_1/?param_1=5&param_2=d HTTP/1.1" 200
      INFO   127.0.0.1:61238 - "GET /endpoint_1/?param_1=6&param_2=d HTTP/1.1" 200
      INFO   127.0.0.1:61242 - "GET /endpoint_1/?param_1=7&param_2=d HTTP/1.1" 200
```
