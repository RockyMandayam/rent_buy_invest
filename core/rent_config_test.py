import jsonschema

from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils import io_utils

TEST_SCHEMA_PATH = "rent_buy_invest/configs/schemas/rent-config-schema.json"
TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-rent-config.yaml"
rent_config_schema = io_utils.read_json(TEST_SCHEMA_PATH)
rent_config_kwargs = io_utils.read_yaml(TEST_CONFIG_PATH)
jsonschema.validate(instance=rent_config_kwargs, schema=rent_config_schema)
# tests creating MarketConfig directly
rent_config = RentConfig(**rent_config_kwargs)
# tests creating MarketConfig via parse()
rent_config = RentConfig.parse(TEST_CONFIG_PATH)


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
