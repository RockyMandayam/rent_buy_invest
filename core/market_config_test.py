import jsonschema
import pytest

from rent_buy_invest.core.market_config import MarketConfig

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-market-config.yaml"
MARKET_CONFIG = MarketConfig.parse(TEST_CONFIG_PATH)


class TestMarketConfig:
    # TODO test edge cases

    def test_inputs_with_invalid_schema(self) -> None:
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_null_market_rate_of_return.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_null_tax_brackets.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_null_tax_brackets_2.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_empty_tax_brackets.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_null_upper_limit.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            MarketConfig.parse(
                "rent_buy_invest/core/test_resources/test-market-config_null_tax_rate.yaml"
            )

    def test_get_tax(self) -> None:
        assert MARKET_CONFIG.get_tax(0) == pytest.approx(0)
        assert MARKET_CONFIG.get_tax(44625) == pytest.approx(0)
        assert MARKET_CONFIG.get_tax(500000) == pytest.approx(68691.25)

    def test_get_pretax_monthly_wealth(self) -> None:
        actual = MARKET_CONFIG.get_pretax_monthly_wealth(100, 1)
        expected = [pytest.approx(100)]
        assert actual == expected
        num_months = 25
        actual = MARKET_CONFIG.get_pretax_monthly_wealth(100, num_months)
        expected = [
            pytest.approx(round((1.07) ** (i / 12) * 100, 2)) for i in range(num_months)
        ]
        assert actual == expected
