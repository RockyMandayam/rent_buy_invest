from typing import Any, Dict, List, Optional

import csv
import yaml


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
