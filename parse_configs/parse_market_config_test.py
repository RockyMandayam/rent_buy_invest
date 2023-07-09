
import pytest
import yaml

import parse_market_config

class TestMarketConfig():

	def test_get_tax(self) -> None:
		# TODO don't use absolute path
		# TODO use parse_market_config and pass in test config path
		with open("/Users/rocky/Downloads/rent_buy_invest/parse_configs/test_config_files/2023-market-config.yaml") as f:
			market_config = yaml.load(f)
		# assert market_config.get_tax(0) == 0
		assert market_config.get_tax(44625) == pytest.approx(0)
		assert market_config.get_tax(500000) == pytest.approx(68691.25)
