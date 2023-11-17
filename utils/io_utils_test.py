import os
from typing import Any, Dict

from rent_buy_invest.utils import io_utils

TEST_YAML_PATH = "rent_buy_invest/utils/test_resources/simple-yaml.yaml"
TEST_JSON_PATH = "rent_buy_invest/utils/test_resources/simple-json.json"


def test_get_abs_path() -> None:
    relative_path = "rent_buy_invest/configs"
    actual = io_utils.get_abs_path(relative_path)
    # TODO do not hardcode this - should work on any machine
    expected = "/Users/rocky/Downloads/rent_buy_invest/configs"
    assert actual == expected


def test_make_dirs() -> None:
    project_path_dir = "rent_buy_invest/test_dir/"
    io_utils.make_dirs(project_path_dir)
    abs_path_dir = io_utils.get_abs_path(project_path_dir)
    assert os.path.isdir(abs_path_dir)
    io_utils.delete_dir


def test_read_yaml() -> None:
    # simple custom test case
    actual = io_utils.read_yaml(TEST_YAML_PATH)
    expected = {
        "a": 1,
        "b": 1.1,
        "c": "1",
        "d": [True, False],
    }
    assert actual == expected

    # try reading example yamls
    io_utils.read_yaml(
        "rent_buy_invest/configs/examples/experiment-config-example-1.yaml"
    )
    io_utils.read_yaml("rent_buy_invest/configs/examples/house-config-example-1.yaml")
    io_utils.read_yaml("rent_buy_invest/configs/examples/market-config-example-1.yaml")
    io_utils.read_yaml("rent_buy_invest/configs/examples/rent-config-example-1.yaml")


def test_write_yaml() -> None:
    # simple custom test case
    exp = {
        "a": 1,
        "b": 1.1,
        "c": "1",
        "d": [True, False],
    }
    dir = f"rent_buy_invest/temp/test_write_yaml/"
    project_path = f"{dir}/test_write_yaml.yaml"
    io_utils.make_dirs(dir, exist_ok=True)
    io_utils.write_yaml(project_path, exp)
    act = io_utils.read_yaml(project_path)
    assert act == exp
    io_utils.delete_file(project_path)


# TODO test write_csv_df


def test_read_json() -> None:
    # simple custom test case
    actual = io_utils.read_yaml(TEST_JSON_PATH)
    expected = {
        "a": 1,
        "b": 1.1,
        "c": "1",
        "d": [True, False],
    }
    assert actual == expected

    # try reading example jsons
    io_utils.read_json("rent_buy_invest/configs/schemas/experiment-config-schema.json")
    io_utils.read_json("rent_buy_invest/configs/schemas/house-config-schema.json")
    io_utils.read_json("rent_buy_invest/configs/schemas/market-config-schema.json")
    io_utils.read_json("rent_buy_invest/configs/schemas/rent-config-schema.json")
