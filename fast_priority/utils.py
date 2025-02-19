import httpx


def generate_enpoint_list(raw_endpoint_str: str | None) -> list[str]:
    ret = []
    if raw_endpoint_str:
        ret = [
            p.strip() for p in raw_endpoint_str.strip().split(",") if p not in {"", " "}
        ]

    return ret


def run_request(method: str, url: str, headers: dict, content: dict):
    # print(f"Got: {method=}, {url=}")
    with httpx.Client(timeout=None, follow_redirects=True) as client:
        return client.request(method=method, url=url, headers=headers, content=content)
