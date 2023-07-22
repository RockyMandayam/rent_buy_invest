from typing import Any, Dict

import yaml

from rent_buy_invest.utils import io_utils

TEST_YAML_PATH = "rent_buy_invest/utils/test_resources/simple-yaml.yaml"


def test_get_abs_path() -> None:
    relative_path = "rent_buy_invest/configs"
    actual = io_utils._get_abs_path(relative_path)
    # TODO is there any way not to hard code this?
    expected = "/Users/rocky/Downloads/rent_buy_invest/configs"
    assert actual == expected


def test_read_yaml() -> None:
    actual = io_utils.read_yaml(TEST_YAML_PATH)
    expected = {
        "a": 1,
        "b": 1.1,
        "c": "1",
        "d": [True, False],
    }
    assert actual == expected
