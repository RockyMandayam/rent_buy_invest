import jsonschema
import pytest

from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.utils import io_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/2023-market-config.yaml"
market_config_kwargs = io_utils.read_yaml(TEST_CONFIG_PATH)
TEST_SCHEMA_PATH = "rent_buy_invest/configs/schemas/market-config-schema.json"
market_config_schema = io_utils.read_json(TEST_SCHEMA_PATH)
jsonschema.validate(instance=market_config_kwargs, schema=market_config_schema)

# tests creating MarketConfig directly
market_config = MarketConfig(**market_config_kwargs)

# tests creating MarketConfig via parse()
market_config = MarketConfig.parse(TEST_CONFIG_PATH)


class TestMarketConfig:
    # TODO test edge cases

    def test_get_tax(self) -> None:
        assert market_config.get_tax(0) == pytest.approx(0)
        assert market_config.get_tax(44625) == pytest.approx(0)
        assert market_config.get_tax(500000) == pytest.approx(68691.25)

    def test_get_pretax_monthly_wealth(self) -> None:
        actual = market_config.get_pretax_monthly_wealth(100, 1)
        expected = [pytest.approx(100)]
        assert actual == expected
        num_months = 25
        actual = market_config.get_pretax_monthly_wealth(100, num_months)
        expected = [
            pytest.approx(round((1.07) ** (i / 12) * 100, 2)) for i in range(num_months)
        ]
        assert actual == expected
