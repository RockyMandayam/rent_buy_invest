from typing import Any, Dict

import yaml

from . import io_utils, path_utils


def test_load_yaml() -> None:
    filename = path_utils.get_abs_path(
        "rent_buy_invest/utils/test_resources/simple-yaml.yaml"
    )
    with open(filename) as f:
        actual: Dict[str, Any] = yaml.load(f, Loader=yaml.SafeLoader)
    expected = {
        "a": 1,
        "b": 1.1,
        "c": "1",
        "d": [True, False],
    }
    assert actual == expected
