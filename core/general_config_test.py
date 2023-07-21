from typing import Any, Dict

import yaml

from ..utils import io_utils, path_utils
from .general_config import GeneralConfig


class TestGeneralConfig:
    def test_parse(self) -> None:
        filename = path_utils.get_abs_path("rent_buy_invest/core/test_resources/test-general-config.yaml")
        GeneralConfig.parse(filename)
