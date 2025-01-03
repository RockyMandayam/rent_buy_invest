import copy

import jsonschema
import pytest

from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.utils_for_testing import check_float_field
from rent_buy_invest.utils import io_utils
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-market-config.yaml"
MARKET_CONFIG = MarketConfig.parse(TEST_CONFIG_PATH)


class TestMarketConfig:
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

        check_float_field(
            MarketConfig,
            config_kwargs,
            ["market_rate_of_return"],
            max_value=MarketConfig.MAX_MARKET_RATE_OF_RETURN,
        )
        num_brackets = len(config_kwargs["tax_brackets"]["tax_brackets"])
        # for all non-highest brackets, check upper limit and tax rate
        for bracket_index in range(num_brackets - 1):
            check_float_field(
                MarketConfig,
                config_kwargs,
                ["tax_brackets", "tax_brackets", bracket_index, "upper_limit"],
                allow_negative=False,
                allow_zero=False,
            )
            check_float_field(
                MarketConfig,
                config_kwargs,
                ["tax_brackets", "tax_brackets", bracket_index, "tax_rate"],
                allow_negative=False,
                allow_greater_than_one=False,
            )
        # for highest bracket, upper limit is infinity, and check tax rate in the same way
        invalid_kwargs = copy.deepcopy(config_kwargs)
        invalid_kwargs["tax_brackets"]["tax_brackets"].pop()
        with pytest.raises(AssertionError):
            MarketConfig(**invalid_kwargs)
        check_float_field(
            MarketConfig,
            config_kwargs,
            ["tax_brackets", "tax_brackets", bracket_index, "tax_rate"],
            allow_negative=False,
        )

        # non-increasing upper_limit should cause error
        invalid_kwargs = copy.deepcopy(config_kwargs)
        invalid_kwargs["tax_brackets"]["tax_brackets"][1]["upper_limit"] = 44625
        with pytest.raises(AssertionError):
            MarketConfig(**invalid_kwargs)

        # test regressive tax brackets
        invalid_kwargs["tax_brackets"]["tax_brackets"][1]["tax_rate"] = 0.0
        invalid_kwargs["validate_non_regressive_tax_brackets"] = True
        with pytest.raises(AssertionError):
            MarketConfig(**invalid_kwargs)

    def test_get_tax(self) -> None:
        with pytest.raises(AssertionError):
            MARKET_CONFIG.get_tax(-1)
        assert MARKET_CONFIG.get_tax(0) == pytest.approx(0)
        assert MARKET_CONFIG.get_tax(44625) == pytest.approx(0)
        assert MARKET_CONFIG.get_tax(500000) == pytest.approx(68691.25)

    def test_get_pretax_monthly_wealth(self) -> None:
        with pytest.raises(AssertionError):
            MARKET_CONFIG.get_pretax_monthly_wealth(-1, 12)
        with pytest.raises(AssertionError):
            MARKET_CONFIG.get_pretax_monthly_wealth(100, 0)

        assert MARKET_CONFIG.get_pretax_monthly_wealth(0, 12) == [0] * 13

        for num_months in [1, 2, 24, 25]:
            actual = MARKET_CONFIG.get_pretax_monthly_wealth(100, num_months)
            expected = [
                pytest.approx(round((1.07) ** (i / MONTHS_PER_YEAR) * 100, 2))
                for i in range(num_months + 1)
            ]
            assert actual == expected
