from copy import deepcopy

import jsonschema
import pytest

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.config_test import TestConfig
from rent_buy_invest.configs.utils_for_testing import check_float_field
from rent_buy_invest.utils import io_utils


class TestBuyConfig(TestConfig):
    TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-buy-config.yaml"
    BUY_CONFIG = BuyConfig.parse(TEST_CONFIG_PATH)

    def test_inputs_with_invalid_schema(self) -> None:
        # check missing and null fields
        attributes = [
            "sale_price",
            "annual_assessed_value_inflation_rate",
            "down_payment_fraction",
            "mortgage_annual_interest_rate",
            "mortgage_term_months",
            "upfront_mortgage_insurance_fraction",
            "annual_mortgage_insurance_fraction",
            "is_fha_loan",
            "mortgage_origination_points_fee_fraction",
            "mortgage_processing_fee",
            "mortgage_underwriting_fee",
            "mortgage_discount_points_fee_fraction",
            "home_appraisal_cost",
            "credit_report_fee",
            "flood_certification_fee",
            "transfer_tax_fraction",
            "seller_burden_of_transfer_tax_fraction",
            "recording_fee_fraction",
            "annual_property_tax_rate",
            "buyer_realtor_commission_fraction",
            "seller_realtor_commission_fraction",
            "hoa_transfer_fee",
            "seller_burden_of_hoa_transfer_fee",
            "home_inspection_cost",
            "pest_inspection_cost",
            "seller_one_time_home_warranty",
            "escrow_fixed_fee",
            "seller_burden_of_escrow_fixed_fee",
            "title_search_fee",
            "seller_burden_of_title_search_fee",
            "title_search_abstract_fee",
            "seller_burden_of_title_search_abstract_fee",
            "title_courier_fee",
            "buyer_attorney_fee",
            "seller_attorney_fee",
            "lenders_title_insurance_fraction",
            "owners_title_insurance_fraction",
            "endorsement_fees",
            "closing_protection_letter_fee",
            "survey_fee",
            "notary_fee",
            "seller_deed_prep_fee",
            "seller_natural_hazard_report_fee",
            "annual_homeowners_insurance_fraction",
            "annual_flood_insurance",
            "monthly_utilities",
            "annual_maintenance_cost_fraction",
            "annual_home_warranty",
            "monthly_hoa_fees",
            "rental_income_config",
            ("rental_income_config", "annual_management_cost_fraction"),
            ("rental_income_config", "rental_income_waiting_period_months"),
            ("rental_income_config", "monthly_rental_income"),
            ("rental_income_config", "rental_income_annual_inflation_rate"),
            ("rental_income_config", "occupancy_rate"),
        ]
        nullable_attributes = ("rental_income_config",)
        self._test_inputs_with_invalid_schema(
            BuyConfig, attributes, nullable_attributes
        )

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TestBuyConfig.TEST_CONFIG_PATH)
        test_buy_config = BuyConfig(**config_kwargs)

        check_float_field(
            BuyConfig,
            config_kwargs,
            ["sale_price"],
            allow_negative=False,
            allow_zero=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_assessed_value_inflation_rate"],
            max_value=BuyConfig.MAX_ANNUAL_RENT_INFLATION_RATE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["down_payment_fraction"],
            allow_negative=False,
            allow_greater_than_one=False,
        )

        check_float_field(
            BuyConfig,
            config_kwargs,
            ["mortgage_annual_interest_rate"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MORTGAGE_ANNUAL_INTEREST_RATE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["mortgage_term_months"],
            allow_negative=False,
            allow_zero=False,
            max_value=BuyConfig.MAX_MORTGAGE_TERM,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["upfront_mortgage_insurance_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_UPFRONT_MORTGAGE_INSURANCE_FRACTION
            * test_buy_config.initial_loan_amount,
        ),
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_mortgage_insurance_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_MORTGAGE_INSURANCE_FRACTION
            * test_buy_config.initial_loan_amount,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["mortgage_origination_points_fee_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MORTGAGE_ORIGINATION_POINTS_FEE_FRACTION
            * test_buy_config.initial_loan_amount,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["mortgage_processing_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MORTGAGE_PROCESSING_FEE
            * test_buy_config.initial_loan_amount,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["mortgage_underwriting_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MORTGAGE_UNDERWRITING_FEE
            * test_buy_config.initial_loan_amount,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["mortgage_discount_points_fee_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MORTGAGE_DISCOUNT_POINTS_FEE_FRACTION
            * test_buy_config.initial_loan_amount,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["home_appraisal_cost"],
            allow_negative=False,
            max_value=BuyConfig.MAX_HOME_APPRAISAL_COST,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["credit_report_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_CREDIT_REPORT_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["flood_certification_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_FLOOD_CERTIFICATION_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["transfer_tax_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_TRANSFER_TAX_FRACTION,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_burden_of_transfer_tax_fraction"],
            allow_negative=False,
            allow_greater_than_one=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["recording_fee_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_RECORDING_FEE_FRACTION,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_property_tax_rate"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_PROPERTY_TAX_RATE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["buyer_realtor_commission_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_REALTOR_COMMISSION_FRACTION,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_realtor_commission_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_REALTOR_COMMISSION_FRACTION,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["hoa_transfer_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_HOA_TRANSFER_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_burden_of_hoa_transfer_fee"],
            allow_negative=False,
            allow_greater_than_one=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["home_inspection_cost"],
            allow_negative=False,
            max_value=BuyConfig.MAX_HOME_INSPECTION_COST,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["pest_inspection_cost"],
            allow_negative=False,
            max_value=BuyConfig.MAX_PEST_INSPECTION_COST,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_one_time_home_warranty"],
            allow_negative=False,
            # TODO max value
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["escrow_fixed_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ESCROW_FIXED_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_burden_of_escrow_fixed_fee"],
            allow_negative=False,
            allow_greater_than_one=False,
            # TODO max value
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["title_search_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_TITLE_SEARCH_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_burden_of_title_search_fee"],
            allow_negative=False,
            allow_greater_than_one=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["title_search_abstract_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_SEARCH_ABSTRACT_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_burden_of_title_search_abstract_fee"],
            allow_negative=False,
            allow_greater_than_one=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["title_courier_fee"],
            allow_negative=False,
            # TODO max value
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["buyer_attorney_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ATTORNEY_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_attorney_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ATTORNEY_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["lenders_title_insurance_fraction"],
            allow_negative=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["owners_title_insurance_fraction"],
            allow_negative=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["endorsement_fees"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ENDORSEMENT_FEES,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["closing_protection_letter_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_CLOSING_PROTECTION_LETTER_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["survey_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_SURVEY_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["notary_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_NOTARY_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_deed_prep_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_DEED_PREP_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_natural_hazard_report_fee"],
            allow_negative=False,
            # TODO max value
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_homeowners_insurance_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_HOMEOWNERS_INSURANCE_FRACTION,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_flood_insurance"],
            allow_negative=False,
            # TODO max value
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["monthly_utilities"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MONTHLY_UTILITIES,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_maintenance_cost_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_MAINTENANCE_COST_FRACTION,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_home_warranty"],
            allow_negative=False,
            # TODO max limit
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["monthly_hoa_fees"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MONTHLY_HOA_FEES,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_config", "annual_management_cost_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_MANAGEMENT_COST_FRACTION,
        )

        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_config", "rental_income_waiting_period_months"],
            allow_negative=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_config", "monthly_rental_income"],
            allow_negative=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_config", "rental_income_annual_inflation_rate"],
            max_value=BuyConfig.MAX_MONTHLY_RENTAL_INCOME_INFLATION_RATE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_config", "occupancy_rate"],
            allow_greater_than_one=False,
        )

    def test_get_monthly_rental_incomes(self) -> None:
        buy_config_copy = deepcopy(TestBuyConfig.BUY_CONFIG)
        with pytest.raises(AssertionError):
            buy_config_copy.get_monthly_rental_incomes(0)
        # TODO since I now do personal or investment use but not both, I don't need a waiting period!
        # no rental income for the first 24 months (waiting period)
        assert buy_config_copy.get_monthly_rental_incomes(1) == [0, 0]
        assert buy_config_copy.get_monthly_rental_incomes(23) == [0 for _ in range(24)]
        # average rental income after waiting period, accounting for occupancy rate
        rental_income = round(0.6 * 1000 * (1 + 0.02) ** 2, 2)
        assert buy_config_copy.get_monthly_rental_incomes(24) == pytest.approx(
            [0 for _ in range(24)] + [rental_income]
        )
        # rental income should only increase annually
        assert buy_config_copy.get_monthly_rental_incomes(35) == pytest.approx(
            [0 for _ in range(24)] + [rental_income for _ in range(12)]
        )
        next_year_rental_income = round(rental_income * (1 + 0.02), 2)
        assert buy_config_copy.get_monthly_rental_incomes(36) == pytest.approx(
            [0 for _ in range(24)]
            + [rental_income for _ in range(12)]
            + [next_year_rental_income]
        )

    def test_get_monthly_mortgage_payment(self) -> None:
        # Sale price is $500,000. Down payment is 20%. So initial loan amount is $400,000
        # Mortgage term is 360 months
        # Annual interest rate is 0.06
        actual = TestBuyConfig.BUY_CONFIG.get_monthly_mortgage_payment()
        expected = 2398.20
        assert actual == expected

    def test_get_upfront_one_time_cost(self) -> None:
        actual = TestBuyConfig.BUY_CONFIG.get_upfront_one_time_cost()
        expected = (
            0.015 * 400000
            + 300
            + 500
            + 0.005 * 400000
            + 500
            + 50
            + (1 - 0.9) * 0.0011 * 500000
            + (0.03 * 500000)
            + (0.025 * 500000)
            + (1 - 1.0) * 300
            + 500
            + 500
            + 500
            + 20
            + (1 - 1) * 100
            + 800
            + 35
            + 300
            + 500
            + 100
            + 50
            + 0.02 * 400000
            + 0.01 * 400000
            + 150
        )
        assert actual == expected
