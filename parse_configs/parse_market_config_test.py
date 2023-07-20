import pytest
import yaml

from . import parse_market_config


class TestMarketConfig:
    # TODO test edge cases

    def test_get_tax(self) -> None:
        # TODO don't use absolute path
        # TODO use parse_market_config and pass in test config path
        with open(
            "/Users/rocky/Downloads/rent_buy_invest/parse_configs/test_config_files/2023-market-config.yaml"
        ) as f:
            market_config = yaml.load(f, Loader=yaml.Loader)
        # assert market_config.get_tax(0) == 0
        assert market_config.get_tax(44625) == pytest.approx(0)
        assert market_config.get_tax(500000) == pytest.approx(68691.25)

    def test_get_pretax_monthly_wealth(self) -> None:
        # TODO don't use absolute path
        # TODO use parse_market_config and pass in test config path
        # TODO don't do this in every test, just do it once
        with open(
            "/Users/rocky/Downloads/rent_buy_invest/parse_configs/test_config_files/2023-market-config.yaml"
        ) as f:
            market_config = yaml.load(f, Loader=yaml.Loader)
        actual = market_config.get_pretax_monthly_wealth(100, 1)
        expected = [pytest.approx(100)]
        assert actual == expected
        actual = market_config.get_pretax_monthly_wealth(100, 13)
        expected = [
            pytest.approx(round((1.07) ** (i / 12) * 100, 2)) for i in range(13)
        ]
        assert actual == expected
