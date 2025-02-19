import pytest

from fast_priority.utils import generate_enpoint_list


@pytest.mark.parametrize(
    ("str_in", "exp_list"),
    [
        (None, []),
        ("", []),
        (", ", []),
        (" , , , ", []),
        ("aaa", ["aaa"]),
        ("aaa,", ["aaa"]),
        ("aaa   ", ["aaa"]),
        ("aaa  , bbb ", ["aaa", "bbb"]),
    ],
)
def test_generate_endpoint_list(str_in: str | None, exp_list: list[str]) -> None:
    act_list = generate_enpoint_list(str_in)

    assert isinstance(act_list, list)

    assert len(act_list) == len(exp_list)
    assert sorted(act_list) == sorted(exp_list)
