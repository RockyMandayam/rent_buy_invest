import itertools

import jsonschema
import pytest

from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.core.utils_for_testing import check_float_field
from rent_buy_invest.utils import io_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-rent-config.yaml"
RENT_CONFIG = RentConfig.parse(TEST_CONFIG_PATH)


class TestRentConfig:
    # TODO test edge cases

    def test_inputs_with_invalid_schema(self) -> None:
        # check null fields
        attributes = [
            "monthly_rent",
            "monthly_utilities",
            "monthly_renters_insurance",
            "monthly_parking_fee",
            "annual_rent_inflation_rate",
            "inflation_adjustment_period",
            "security_deposit",
            "unrecoverable_fraction_of_security_deposit",
        ]
        for attribute in attributes:
            test_config_filename = f"rent_buy_invest/core/test_resources/test-rent-config_null_{attribute}.yaml"
            with pytest.raises(jsonschema.ValidationError):
                RentConfig.parse(test_config_filename)

        # check missing field
        with pytest.raises(jsonschema.ValidationError):
            RentConfig.parse(
                "rent_buy_invest/core/test_resources/test-rent-config_missing_inflation_adjustment_period.yaml"
            )

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TEST_CONFIG_PATH)

        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_rent"],
            allow_negative=False,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_utilities"],
            allow_negative=False,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_renters_insurance"],
            allow_negative=False,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_parking_fee"],
            allow_negative=False,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["annual_rent_inflation_rate"],
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["inflation_adjustment_period"],
            allow_negative=False,
            allow_zero=False,
        )

    def test_get_upfront_one_time_cost(self) -> None:
        act = RENT_CONFIG.get_upfront_one_time_cost()
        exp = (
            RENT_CONFIG.security_deposit
            * RENT_CONFIG.unrecoverable_fraction_of_security_deposit
        )
        assert act == exp

    def test_get_monthly_costs_of_renting(self) -> None:
        for num_months in [1, 2, 24, 25]:
            actual = RENT_CONFIG.get_monthly_costs_of_renting(num_months)

            num_full_years = num_months // 12
            exp = []
            # calculate for all but last year
            for year in range(num_full_years):
                monthly_rent = round(
                    2420.0 * (1 + RENT_CONFIG.annual_rent_inflation_rate) ** year,
                    2,
                )
                exp.extend([monthly_rent] * 12)
            # calculate for last year
            monthly_rent = round(
                2420.0 * (1 + RENT_CONFIG.annual_rent_inflation_rate) ** num_full_years,
                2,
            )
            exp.extend([monthly_rent] * (num_months % 12))

            assert actual == exp
