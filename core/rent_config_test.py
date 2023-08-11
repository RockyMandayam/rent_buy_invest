import jsonschema
import pytest

from rent_buy_invest.core.rent_config import RentConfig

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-rent-config.yaml"
RENT_CONFIG = RentConfig.parse(TEST_CONFIG_PATH)


class TestRentConfig:
    # TODO test edge cases

    def test_inputs_with_invalid_schema(self) -> None:
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_null_monthly_rent.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_null_monthly_utilities.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_null_monthly_renters_insurance.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_null_monthly_parking_fee.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_null_annual_rent_inflation_rate.yaml"
            )
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_null_inflation_adjustment_period.yaml"
            )

    def test_get_monthly_costs_of_renting(self) -> None:
        actual = RENT_CONFIG.get_monthly_costs_of_renting(25)
        expected = (
            [2420.0] * 12
            + [round(2420.0 * 1.03, 2)] * 12
            + [round(2420.0 * 1.03**2, 2)]
        )
        assert actual == expected
