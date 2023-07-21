import yaml

from ..utils import io_utils
from .rent_config import RentConfig

# TODO don't use absolute path
filename = (
    "/Users/rocky/Downloads/rent_buy_invest/core/test_resources/test-rent-config.yaml"
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
