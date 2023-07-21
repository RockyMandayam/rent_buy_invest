from typing import Any, Dict

import yaml

from ..utils import io_utils
from .general_config import GeneralConfig


class TestGeneralConfig:
    def test_parse(self) -> None:
    	# TODO don't use absolute path
        filename = "/Users/rocky/Downloads/rent_buy_invest/core/test_resources/test-general-config.yaml"
        GeneralConfig.parse(filename)
