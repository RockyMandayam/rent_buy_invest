from rent_buy_invest.utils import path_utils


def test_get_abs_path() -> None:
    relative_path = "rent_buy_invest/configs"
    actual = path_utils.get_abs_path(relative_path)
    # TODO is there any way not to hard code this?
    expected = "/Users/rocky/Downloads/rent_buy_invest/configs"
    assert actual == expected
