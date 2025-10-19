import os

import pandas as pd

from rent_buy_invest.io import io_utils

TEST_YAML_PATH = "rent_buy_invest/utils/test_resources/simple-yaml.yaml"
TEST_JSON_PATH = "rent_buy_invest/utils/test_resources/simple-json.json"
EXPECTED_TEST_VALUE = {
    "a": 1,
    "b": 1.1,
    "c": "1",
    "d": [True, False],
}


def test_get_abs_path() -> None:
    relative_path = "rent_buy_invest/configs"
    actual = io_utils.get_abs_path(relative_path)
    expected = [
        "/Users/rockymandayam/Downloads/rent_buy_invest/src/rent_buy_invest/configs",  # local dev machine for Rocky
        "/home/runner/work/rent_buy_invest/rent_buy_invest/src/rent_buy_invest/configs",  # github action machine
    ]
    assert actual in expected


def test_make_dirs_and_remove_dirs() -> None:
    project_path_dir = "rent_buy_invest/temp/test_dir/"
    io_utils.make_dirs(project_path_dir)
    abs_path_dir = io_utils.get_abs_path(project_path_dir)
    assert os.path.isdir(abs_path_dir)
    io_utils.delete_dir(project_path_dir)
    assert not os.path.isdir(abs_path_dir)


def test_read_yaml_and_write_yaml() -> None:
    # simple yaml test
    actual = io_utils.read_yaml(TEST_YAML_PATH)
    assert actual == EXPECTED_TEST_VALUE
    # ideally, write it and check equality, but two files can be formatted differently with the same content
    # so, write and read again, and check that it's the same
    dir = f"rent_buy_invest/temp/test_write_yaml"
    project_path = f"{dir}/test_write_yaml.yaml"
    io_utils.write_yaml(project_path, actual)
    reread_actual = io_utils.read_yaml(project_path)
    assert reread_actual == actual

    # similarly, but without an expected result for the first read, check write+read idempotency
    # for the config classes
    for yaml_path in (
        "rent_buy_invest/core/test_resources/test-experiment-config.yaml",
        "rent_buy_invest/core/test_resources/test-buy-config.yaml",
        "rent_buy_invest/core/test_resources/test-market-config.yaml",
        "rent_buy_invest/core/test_resources/test-rent-config.yaml",
    ):
        actual = io_utils.read_yaml(yaml_path)
        io_utils.write_yaml(project_path, actual)
        reread_actual = io_utils.read_yaml(project_path)
    io_utils.delete_dir(dir)


def test_write_xlsx_df() -> None:
    dir = f"rent_buy_invest/temp/test_write_xlsx_df"
    project_path = f"{dir}/test_write_xlsx_df.xlsx"
    io_utils.make_dirs(dir, exist_ok=True)

    # test basic DataFrame
    exp = pd.DataFrame(
        {
            "col1": [1, 2],
            "col2": [3, 4],
        }
    )
    io_utils.write_xlsx_df(project_path, exp)
    act = pd.read_excel(io_utils.get_abs_path(project_path), index_col=0)
    assert act.equals(exp)

    # test multi-index column
    exp = pd.DataFrame(
        {
            ("category 1", "col1"): [1, 2],
            ("category 2", "col2"): [3, 4],
        }
    )
    io_utils.write_xlsx_df(project_path, exp)
    act = pd.read_excel(io_utils.get_abs_path(project_path), index_col=0, header=[0, 1])
    assert act.equals(exp)

    io_utils.delete_dir(dir)


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
    io_utils.read_json("rent_buy_invest/configs/schemas/buy-config-schema.json")
    io_utils.read_json("rent_buy_invest/configs/schemas/market-config-schema.json")
    io_utils.read_json("rent_buy_invest/configs/schemas/rent-config-schema.json")
