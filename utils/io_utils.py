import json
import os
from typing import Any, Dict, List, Union

import pandas as pd
import yaml


def _get_abs_path(project_path: str) -> str:
    """Returns the absolute path given relative path.

    Args:
        project_path (str): path starting with top-level directory.

    Returns:
        str: absolute path

    Examples:
    >>> _get_abs_path("rent_buy_invest/configs")
    '/Users/FooBarUser/rent_buy_invest/configs'
    """
    # TODO is there any way not to hard code this?
    if not project_path.startswith("rent_buy_invest"):
        raise ValueError("Invalid project_path")
    dir_containing_top_level_dir = os.path.join(
        os.path.join(os.path.dirname(__file__), ".."), ".."
    )
    dir_containing_top_level_dir = os.path.abspath(dir_containing_top_level_dir)
    return os.path.join(os.path.abspath(dir_containing_top_level_dir), project_path)


def make_dirs(project_path: str) -> None:
    os.makedirs(_get_abs_path(project_path))


def read_yaml(project_path: str) -> Union[Dict[str, Any], List]:
    """Load yaml given by path (from top-level directory) as dictionary."""
    abs_path = _get_abs_path(project_path)
    with open(abs_path, mode="r") as f:
        # TODO load is unsafe apparently! use safe_load!
        general_config: Dict[str, Any] = yaml.load(f, Loader=yaml.SafeLoader)
    return general_config


def write_yaml(project_path: str, obj: Any) -> None:
    """Write objct to given path (from top-level directory) as yaml."""
    abs_path = _get_abs_path(project_path)
    with open(abs_path, mode="x") as f:
        yaml.dump(obj, f)


# TODO use a context manager to always write from relative paths?
def write_csv_df(project_path: str, df: pd.DataFrame) -> None:
    abs_path = _get_abs_path(project_path)
    abs_path = abs_path[:-3] + "xlsx"
    df.to_excel(abs_path)


def read_json(project_path: str) -> Union[Dict, List]:
    abs_path = _get_abs_path(project_path)
    with open(abs_path, mode="r") as f:
        return json.load(f)
