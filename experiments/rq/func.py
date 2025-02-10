from time import sleep

import httpx


def run_get_request(url):
    sleep(3)
    with httpx.Client(timeout=None) as client:
        return client.get(url)
