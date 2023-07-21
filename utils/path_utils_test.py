from . import path_utils


def test_get_abs_path() -> None:
    relative_path = "rent_buy_invest/configs"
    actual = path_utils.get_abs_path(relative_path)
    # TODO fix this using PYTHONPATH or something later. When I get to that stuff
    expected = "/Users/rocky/Downloads/rent_buy_invest/configs"
    assert actual == expected
