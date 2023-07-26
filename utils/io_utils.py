import csv
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from rent_buy_invest.utils import io_utils


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


def read_yaml(project_path: str) -> Dict[str, Any]:
    """Load yaml given by path (from top-level directory) as dictionary."""
    abs_path = _get_abs_path(project_path)
    with open(abs_path, mode="r") as f:
        general_config: Dict[str, Any] = yaml.load(f, Loader=yaml.SafeLoader)
    return general_config


# TODO test this
def write_yaml(project_path: str, obj: Any) -> None:
    """Write objct to given path (from top-level directory) as yaml."""
    abs_path = _get_abs_path(project_path)
    with open(abs_path, mode="x") as f:
        yaml.dump(obj, f)


# TODO maybe make this a context I can iteratively write to?
# TODO test this
def write_csv(project_path: str, rows: List[List[Optional[Any]]]) -> None:
    """Write the given rows to file with given path."""
    abs_path = _get_abs_path(project_path)
    with open(abs_path, mode="x", newline="") as f:
        writer = csv.writer(f, strict=True)
        for row in rows:
            writer.writerow(row)


# TODO use a context manager to always write from relative paths?
def write_csv_df(project_path: str, df: pd.DataFrame) -> None:
    abs_path = _get_abs_path(project_path)
    df.to_csv(abs_path)
