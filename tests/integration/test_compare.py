import os

import httpx
import pytest

PORT_GATEWAY = os.environ.get("INTEGRATION_TEST_PORT_GATEWAY", 8001)
PORT_API = os.environ.get("INTEGRATION_TEST_PORT_API", 8010)


@pytest.mark.parametrize(
    ("path_and_params", "exp_status"),
    [
        ("endpoint_1?param_1=1&param_2=abc", 200),
        ("endpoint_2?param_1=1&param_2=abc", 200),
        ("sub_category/endpoint_1?param_1=1&param_2=abc", 200),
        ("err_endpoint/?ret_code=500", 500),
        ("err_endpoint/?ret_code=404", 404),
        ("endpoint_2?param_1=1&param_3=1.2", 422),
    ],
)
def test_get(path_and_params: str, exp_status: int) -> None:
    response_direct = httpx.get(
        f"http://localhost:{PORT_API}/{path_and_params}", follow_redirects=True
    )
    response_gateway = httpx.get(
        f"http://localhost:{PORT_GATEWAY}/{path_and_params}", follow_redirects=True
    )

    assert response_gateway.status_code == exp_status
    assert response_direct.status_code == response_gateway.status_code
    assert response_direct.content == response_gateway.content
    assert response_direct.headers.keys() == response_gateway.headers.keys()


@pytest.mark.parametrize(
    ("data", "exp_status"),
    [
        ({"foo": "baz", "bar": 1}, 200),
        ({"foo": "baz"}, 422),
    ],
)
def test_post_valid(data: dict, exp_status: int) -> None:
    path_and_params = "endpoint_3/"
    response_direct = httpx.post(
        f"http://localhost:{PORT_API}/{path_and_params}",
        follow_redirects=True,
        json=data,
    )
    response_gateway = httpx.post(
        f"http://localhost:{PORT_GATEWAY}/{path_and_params}",
        follow_redirects=True,
        json=data,
    )

    print(response_gateway.content)
    assert response_gateway.status_code == exp_status
    assert response_direct.status_code == response_gateway.status_code
    assert response_direct.content == response_gateway.content
    assert response_direct.headers.keys() == response_gateway.headers.keys()
