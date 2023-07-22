import csv
import os
from typing import Any, Dict, List, Optional

import yaml


def get_abs_path(project_path: str) -> str:
    """Returns the absolute path given relative path.

    Args:
        project_path (str): path starting with top-level directory.

    Returns:
        str: absolute path

    Examples:
    >>> get_abs_path("rent_buy_invest/configs")
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


def load_yaml(path: str) -> Dict[str, Any]:
    """Load yaml given by path as dictionary."""
    with open(path) as f:
        general_config: Dict[str, Any] = yaml.load(f, Loader=yaml.SafeLoader)
    return general_config


# TODO maybe make this a context I can iteratively write to?
# TODO test this
def write_csv(path: str, rows: List[List[Optional[str]]]) -> None:
    """Write the given rows to file with given path."""
    with open(path, mode="x", newline="") as f:
        writer = csv.writer(f, strict=True)
        for row in rows:
            writer.writerow(row)
