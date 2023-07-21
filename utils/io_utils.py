from typing import Any, Dict

import yaml


def load_yaml(filename: str) -> Dict[str, Any]:
    with open(filename) as f:
        general_config: Dict[str, Any] = yaml.load(f, Loader=yaml.SafeLoader)
    return general_config
