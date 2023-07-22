from typing import Any, Dict

import yaml

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.utils import io_utils, path_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-house-config.yaml"
house_config = HouseConfig.parse(TEST_CONFIG_PATH)


class TestHouseConfig:
    def test_get_monthly_mortgage_payment(self) -> None:
        # Sale price is $500,000. Down payment is 20%. So loan amount is $400,000
        # Mortgage term is 360 months
        # Annual interest rate is 0.06
        actual = house_config.get_monthly_mortgage_payment()
        expected = 2398.20
        assert actual == expected

    def test_get_upfront_one_time_cost(self) -> None:
        actual = house_config.get_upfront_one_time_cost()
        expected = (
            0.015 * 400000
            + 300
            + 500
            + 0.005 * 400000
            + 500
            + 50
            + (1 - 0.9) * 0.0011 * 500000
            + (0.03 * 500000)
            + (0.025 * 500000)
            + (1 - 1.0) * 300
            + 500
            + 500
            + 500
            + 20
            + (1 - 1) * 100
            + 800
            + 35
            + 300
            + 500
            + 100
            + 50
            + 0.02 * 400000
            + 0.01 * 400000
            + 150
        )
        assert actual == expected
