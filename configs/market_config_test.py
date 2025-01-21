import copy

import jsonschema
import pytest

from rent_buy_invest.configs.config_test import TestConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.utils_for_testing import check_float_field
from rent_buy_invest.utils import io_utils
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


class TestMarketConfig(TestConfig):
    TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-market-config.yaml"
    MARKET_CONFIG = MarketConfig.parse(TEST_CONFIG_PATH)

    def test_inputs_with_invalid_schema(self) -> None:
        attributes = [
            "market_rate_of_return",
            "tax_brackets",
            ("tax_brackets", "income_tax_brackets"),
            ("tax_brackets", "income_tax_brackets", 0, "upper_limit"),
            ("tax_brackets", "income_tax_brackets", 0, "tax_rate"),
            ("tax_brackets", "long_term_capital_gains_tax_brackets"),
            ("tax_brackets", "long_term_capital_gains_tax_brackets", 0, "upper_limit"),
            ("tax_brackets", "long_term_capital_gains_tax_brackets", 0, "tax_rate"),
        ]
        self._test_inputs_with_invalid_schema(MarketConfig, attributes)

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TestMarketConfig.TEST_CONFIG_PATH)

        check_float_field(
            MarketConfig,
            config_kwargs,
            ["market_rate_of_return"],
            max_value=MarketConfig.MAX_MARKET_RATE_OF_RETURN,
        )
        for tax_type in ("income_tax_brackets", "long_term_capital_gains_tax_brackets"):
            num_brackets = len(config_kwargs["tax_brackets"][tax_type])
            # for all non-highest brackets, check upper limit and tax rate
            for bracket_index in range(num_brackets - 1):
                check_float_field(
                    MarketConfig,
                    config_kwargs,
                    ["tax_brackets", tax_type, bracket_index, "upper_limit"],
                    allow_negative=False,
                    allow_zero=False,
                )
                check_float_field(
                    MarketConfig,
                    config_kwargs,
                    ["tax_brackets", tax_type, bracket_index, "tax_rate"],
                    allow_negative=False,
                    allow_greater_than_one=False,
                )
            # for highest bracket, upper limit is infinity, and check tax rate in the same way
            invalid_kwargs = copy.deepcopy(config_kwargs)
            invalid_kwargs["tax_brackets"][tax_type].pop()
            with pytest.raises(AssertionError):
                MarketConfig(**invalid_kwargs)
            check_float_field(
                MarketConfig,
                config_kwargs,
                ["tax_brackets", tax_type, bracket_index, "tax_rate"],
                allow_negative=False,
            )

            # non-increasing upper_limit should cause error
            invalid_kwargs = copy.deepcopy(config_kwargs)
            invalid_kwargs["tax_brackets"][tax_type][1]["upper_limit"] = 44625
            with pytest.raises(AssertionError):
                MarketConfig(**invalid_kwargs)

            # test regressive tax brackets
            invalid_kwargs["tax_brackets"][tax_type][1]["tax_rate"] = 0.0
            invalid_kwargs["validate_non_regressive_tax_brackets"] = True
            with pytest.raises(AssertionError):
                MarketConfig(**invalid_kwargs)

    def test_get_tax(self) -> None:
        with pytest.raises(AssertionError):
            TestMarketConfig.MARKET_CONFIG.get_income_tax(-1)
        assert TestMarketConfig.MARKET_CONFIG.get_income_tax(0) == pytest.approx(0)
        assert TestMarketConfig.MARKET_CONFIG.get_income_tax(44625) == pytest.approx(0)
        assert TestMarketConfig.MARKET_CONFIG.get_income_tax(500000) == pytest.approx(
            68691.25
        )

    def test_get_pretax_monthly_wealth(self) -> None:
        with pytest.raises(AssertionError):
            TestMarketConfig.MARKET_CONFIG.get_pretax_monthly_wealth(-1, 12)
        with pytest.raises(AssertionError):
            TestMarketConfig.MARKET_CONFIG.get_pretax_monthly_wealth(100, 0)

        assert (
            TestMarketConfig.MARKET_CONFIG.get_pretax_monthly_wealth(0, 12) == [0] * 13
        )

        for num_months in [1, 2, 24, 25]:
            actual = TestMarketConfig.MARKET_CONFIG.get_pretax_monthly_wealth(
                100, num_months
            )
            expected = [
                pytest.approx(round((1.07) ** (i / MONTHS_PER_YEAR) * 100, 2))
                for i in range(num_months + 1)
            ]
            assert actual == expected
