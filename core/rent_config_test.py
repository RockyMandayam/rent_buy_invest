import yaml

from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils import io_utils, path_utils

filename = path_utils.get_abs_path(
    "rent_buy_invest/core/test_resources/test-rent-config.yaml"
)
rent_config = RentConfig.parse(filename)


class TestRentConfig:
    # TODO test edge cases

    def test_get_monthly_costs_of_renting(self) -> None:
        actual = rent_config.get_monthly_costs_of_renting(25)
        expected = (
            [2420.0] * 12
            + [round(2420.0 * 1.03, 2)] * 12
            + [round(2420.0 * 1.03**2, 2)]
        )
        assert actual == expected
