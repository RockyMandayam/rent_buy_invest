from typing import Any, Dict

import yaml

from ..utils import io_utils
from .house_config import HouseConfig

class TestHouseConfig:

	def test_parse(self) -> None:
		filename = "/Users/rocky/Downloads/rent_buy_invest/core/test_resources/test-house-config.yaml"
		HouseConfig.parse(filename)
