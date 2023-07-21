import yaml

from . import parse_rent_config


class TestRentConfig:
    # TODO test edge cases

    def test_get_monthly_costs_of_renting(self) -> None:
        # TODO don't use absolute path
        # TODO use parse_rent_config and pass in test config path
        with open(
            "/Users/rocky/Downloads/rent_buy_invest/parse_configs/test_config_files/test-rent-config.yaml"
        ) as f:
            rent_config = yaml.load(f, Loader=yaml.SafeLoader)
        rent_config = parse_rent_config.RentConfig(**rent_config)
        actual = rent_config.get_monthly_costs_of_renting(25)
        expected = (
            [2420.0] * 12
            + [round(2420.0 * 1.03, 2)] * 12
            + [round(2420.0 * 1.03**2, 2)]
        )
        assert actual == expected
