import itertools

import jsonschema
import pytest

from rent_buy_invest.configs.config_test import TestConfig
from rent_buy_invest.configs.rent_config import RentConfig
from rent_buy_invest.configs.utils_for_testing import check_float_field
from rent_buy_invest.io import io_utils
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


class TestRentConfig(TestConfig):
    TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-rent-config.yaml"
    RENT_CONFIG = RentConfig.parse(TEST_CONFIG_PATH)

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
            "subsidy_fraction",
        ]
        self._test_inputs_with_invalid_schema(RentConfig, attributes)

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TestRentConfig.TEST_CONFIG_PATH)

        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_rent"],
            allow_negative=False,
            allow_zero=False,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_utilities"],
            allow_negative=False,
            max_value=RentConfig.MAX_MONTHLY_UTILITIES_AS_FRACTION_OF_RENT
            * config_kwargs["monthly_rent"],
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_renters_insurance"],
            allow_negative=False,
            max_value=RentConfig.MAX_MONTHLY_RENTERS_INSURANCE_AS_FRACTION_OF_RENT
            * config_kwargs["monthly_rent"],
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["monthly_parking_fee"],
            allow_negative=False,
            max_value=RentConfig.MAX_MONTHLY_PARKING_FEE_AS_FRACTION_OF_RENT
            * config_kwargs["monthly_rent"],
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["annual_rent_inflation_rate"],
            max_value=RentConfig.MAX_ANNUAL_RENT_INFLATION_RATE,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["inflation_adjustment_period"],
            allow_negative=False,
            allow_zero=False,
            min_value=1,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["security_deposit"],
            allow_negative=False,
            max_value=RentConfig.MAX_SECURITY_DEPOSIT_AS_FRACTION_OF_RENT
            * config_kwargs["monthly_rent"],
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["unrecoverable_fraction_of_security_deposit"],
            allow_negative=False,
            allow_greater_than_one=False,
        )
        check_float_field(
            RentConfig,
            config_kwargs,
            ["subsidy_fraction"],
            allow_negative=False,
            allow_greater_than_one=False,
        )

    def test_get_upfront_one_time_cost(self) -> None:
        act = TestRentConfig.RENT_CONFIG.get_upfront_one_time_cost()
        exp = (
            TestRentConfig.RENT_CONFIG.security_deposit
            * TestRentConfig.RENT_CONFIG.unrecoverable_fraction_of_security_deposit
        )
        assert act == exp

    def test_get_monthly_costs_of_renting(self) -> None:
        with pytest.raises(AssertionError):
            TestRentConfig.RENT_CONFIG.get_monthly_costs_of_renting(0)

        for num_months in [1, 2, 24, 25]:
            actual = TestRentConfig.RENT_CONFIG.get_monthly_costs_of_renting(num_months)

            num_full_years = num_months // MONTHS_PER_YEAR
            exp = []
            # calculate for all but last year
            for year in range(num_full_years):
                monthly_rent = round(
                    2420.0
                    * (1 + TestRentConfig.RENT_CONFIG.annual_rent_inflation_rate)
                    ** year,
                    2,
                )
                exp.extend([monthly_rent] * MONTHS_PER_YEAR)
            # calculate for last year
            monthly_rent = round(
                2420.0
                * (1 + TestRentConfig.RENT_CONFIG.annual_rent_inflation_rate)
                ** num_full_years,
                2,
            )
            exp.extend([monthly_rent] * ((num_months % MONTHS_PER_YEAR) + 1))

            assert actual == exp
