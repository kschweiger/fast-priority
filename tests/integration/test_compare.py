import os

import httpx
import pytest

PORT_GATEWAY = os.environ.get("INTEGRATION_TEST_PORT_GATEWAY", 8001)
PORT_API = os.environ.get("INTEGRATION_TEST_PORT_API", 8010)


@pytest.mark.parametrize(
    "path_and_params",
    [
        "endpoint_1?param_1=1&param_2=abc",
        "endpoint_2?param_1=1&param_2=abc",
        "sub_category/endpoint_1?param_1=1&param_2=abc",
        "err_endpoint/?ret_code=500",
        "err_endpoint/?ret_code=404",
    ],
)
def test_get(path_and_params: str) -> None:
    response_direct = httpx.get(
        f"http://localhost:{PORT_API}/{path_and_params}", follow_redirects=True
    )
    response_gateway = httpx.get(
        f"http://localhost:{PORT_GATEWAY}/{path_and_params}", follow_redirects=True
    )

    print(response_gateway)
    assert response_direct.status_code == response_gateway.status_code
    assert response_direct.content == response_gateway.content
    assert response_direct.headers.keys() == response_gateway.headers.keys()
