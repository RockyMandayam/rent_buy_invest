import json
import os
from typing import Any, Dict, List, Union

import pandas as pd
import yaml


def get_abs_path(project_path: str) -> str:
    """Returns the absolute path given relative path.

    Args:
        project_path (str): path starting with 'rent_buy_invest' directory.

    Returns:
        str: absolute path

    Examples:
    >>> get_abs_path("rent_buy_invest/configs")
    '/Users/FooBarUser/rent_buy_invest/configs'
    """
    if not project_path.startswith("rent_buy_invest"):
        raise ValueError("Invalid project_path")
    dir_containing_top_level_dir = os.path.join(
        os.path.join(os.path.dirname(__file__), ".."), ".."
    )
    dir_containing_top_level_dir = os.path.abspath(dir_containing_top_level_dir)
    return os.path.join(os.path.abspath(dir_containing_top_level_dir), project_path)


class RentBuyInvestFileOpener:
    """File opener that takes in project path (relative eto rent_buy_invest).

    The default python open() function requires an absolute path.
    """

    def __init__(self, project_path: str, mode: str) -> None:
        self.abs_path = get_abs_path(project_path)
        self.mode = mode

    def __enter__(self) -> Any:
        self.file = open(self.abs_path, mode=self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()


def delete_file(project_path: str) -> None:
    os.remove(get_abs_path(project_path))


def make_dirs(project_path: str, exist_ok: bool = True) -> None:
    os.makedirs(get_abs_path(project_path), exist_ok=exist_ok)


def delete_dir(project_path) -> None:
    os.rmdir(get_abs_path(project_path))


def read_yaml(project_path: str) -> Union[Dict[str, Any], List]:
    """Load yaml given by path (from 'rent_buy_invest' directory) as dictionary."""
    with RentBuyInvestFileOpener(project_path, mode="r") as f:
        general_config: Dict[str, Any] = yaml.load(f, Loader=yaml.SafeLoader)
    return general_config


def write_yaml(project_path: str, obj: Any) -> None:
    """Write object to given path (from 'rent_buy_invest' directory) as yaml.

    project_path should end in '.yaml'
    """
    with RentBuyInvestFileOpener(project_path, mode="w") as f:
        yaml.dump(obj, f)


def write_xlsx_df(project_path: str, df: pd.DataFrame) -> None:
    """Write DataFrame to given path (from the 'rent_buy_invest' directory) as an excel-readable file.

    project_path must end in '.xlsx'
    """
    abs_path = get_abs_path(project_path)
    abs_path = abs_path
    df.style.set_sticky(axis="columns")
    df.style.set_sticky(axis="index")
    df.to_excel(abs_path)


def read_json(project_path: str) -> Union[Dict, List]:
    with RentBuyInvestFileOpener(project_path, mode="r") as f:
        return json.load(f)
