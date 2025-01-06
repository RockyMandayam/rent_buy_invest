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
        # check null fields
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
            "transfer_tax_fraction",
            "seller_burden_of_transfer_tax_fraction",
            "recording_fee_fraction",
            "annual_property_tax_rate",
            "realtor_commission_fraction",
            "hoa_transfer_fee",
            "seller_burden_of_hoa_transfer_fee",
            "home_inspection_cost",
            "pest_inspection_cost",
            "escrow_fixed_fee",
            "flood_certification_fee",
            "title_search_fee",
            "seller_burden_of_title_search_fee_fraction",
            "attorney_fee",
            "closing_protection_letter_fee",
            "search_abstract_fee",
            "survey_fee",
            "notary_fee",
            "deed_prep_fee",
            "lenders_title_insurance_fraction",
            "owners_title_insurance_fraction",
            "endorsement_fees",
            "annual_homeowners_insurance_fraction",
            "monthly_utilities",
            "annual_maintenance_cost_fraction",
            "monthly_hoa_fees",
            "annual_management_cost_fraction",
            "rental_income_waiting_period_months",
            "monthly_rental_income",
            "rental_income_annual_inflation_rate",
            "occupancy_rate",
        ]
        self._test_inputs_with_invalid_schema(BuyConfig, attributes)

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
            ["realtor_commission_fraction"],
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
            ["escrow_fixed_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ESCROW_FIXED_FEE,
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
            ["title_search_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_TITLE_SEARCH_FEE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["seller_burden_of_title_search_fee_fraction"],
            allow_negative=False,
            allow_greater_than_one=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["attorney_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ATTORNEY_FEE,
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
            ["search_abstract_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_SEARCH_ABSTRACT_FEE,
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
            ["deed_prep_fee"],
            allow_negative=False,
            max_value=BuyConfig.MAX_DEED_PREP_FEE,
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
            ["annual_homeowners_insurance_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_HOMEOWNERS_INSURANCE_FRACTION,
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
            ["monthly_hoa_fees"],
            allow_negative=False,
            max_value=BuyConfig.MAX_MONTHLY_HOA_FEES,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["annual_management_cost_fraction"],
            allow_negative=False,
            max_value=BuyConfig.MAX_ANNUAL_MANAGEMENT_COST_FRACTION,
        )

        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_waiting_period_months"],
            allow_negative=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["monthly_rental_income"],
            allow_negative=False,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["rental_income_annual_inflation_rate"],
            max_value=BuyConfig.MAX_MONTHLY_RENTAL_INCOME_INFLATION_RATE,
        )
        check_float_field(
            BuyConfig,
            config_kwargs,
            ["occupancy_rate"],
            allow_greater_than_one=False,
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
