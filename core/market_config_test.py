import copy
from typing import Dict

import jsonschema
import pytest

from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.core.utils_for_testing import check_float_field
from rent_buy_invest.utils import io_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-market-config.yaml"
MARKET_CONFIG = MarketConfig.parse(TEST_CONFIG_PATH)


class TestMarketConfig:
    # TODO test edge cases

    def test_inputs_with_invalid_schema(self) -> None:
        # check null fields
        attributes = [
            "market_rate_of_return",
            "tax_brackets",
            "tax_brackets_2",
            "upper_limit",
            "tax_rate",
        ]
        for attribute in attributes:
            test_config_filename = f"rent_buy_invest/core/test_resources/test-market-config_null_{attribute}.yaml"
            with pytest.raises(jsonschema.ValidationError):
                MarketConfig.parse(test_config_filename)
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_empty_tax_brackets.yaml"
            )

        # check missing field
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_missing_last_tax_rate.yaml"
            )

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TEST_CONFIG_PATH)

        check_float_field(MarketConfig, config_kwargs, ["market_rate_of_return"])
        check_float_field(
            MarketConfig,
            config_kwargs,
            ["tax_brackets", "tax_brackets", 0, "upper_limit"],
            allow_negative=False,
            allow_zero=False,
        )
        check_float_field(
            MarketConfig,
            config_kwargs,
            ["tax_brackets", "tax_brackets", 0, "tax_rate"],
            allow_negative=False,
        )

        # check that there is a final upper limit of infinity
        invalid_kwargs = copy.deepcopy(config_kwargs)
        invalid_kwargs["tax_brackets"]["tax_brackets"].pop()
        with pytest.raises(AssertionError):
            MarketConfig(**invalid_kwargs)

    def test_get_tax(self) -> None:
        assert MARKET_CONFIG.get_tax(0) == pytest.approx(0)
        assert MARKET_CONFIG.get_tax(44625) == pytest.approx(0)
        assert MARKET_CONFIG.get_tax(500000) == pytest.approx(68691.25)

    def test_get_pretax_monthly_wealth(self) -> None:
        for num_months in [1, 2, 24, 25]:
            actual = MARKET_CONFIG.get_pretax_monthly_wealth(100, num_months)
            expected = [
                pytest.approx(round((1.07) ** (i / 12) * 100, 2))
                for i in range(num_months)
            ]
            assert actual == expected
