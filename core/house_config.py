from typing import Any, Dict

import yaml

from rent_buy_invest.core.config import Config
from rent_buy_invest.utils import io_utils, math_utils


class HouseConfig(Config):
    """Stores house config.

    Documentation of the instance variable types:
    # TODO add documentation
    # TODO maybe just point to the yaml file
    """

    def __init__(
        self,
        **kwargs: Dict[str, Any],  # lots of parameters, see body of this method
    ) -> None:
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in GeneralConfig.
        """
        self.sale_price: float = kwargs["sale_price"]
        self.annual_assessed_value_inflation_rate: float = kwargs[
            "annual_assessed_value_inflation_rate"
        ]
        self.down_payment_fraction: float = kwargs["down_payment_fraction"]
        self.mortgage_annual_interest_rate: float = kwargs[
            "mortgage_annual_interest_rate"
        ]
        self.mortgage_term_months: int = kwargs["mortgage_term_months"]
        self.pmi_fraction: float = kwargs["pmi_fraction"]
        self.mortgage_origination_points_fee_fraction: float = kwargs[
            "mortgage_origination_points_fee_fraction"
        ]
        self.mortgage_processing_fee: float = kwargs["mortgage_processing_fee"]
        self.mortgage_underwriting_fee: float = kwargs["mortgage_underwriting_fee"]
        self.mortgage_discount_points_fee_fraction: float = kwargs[
            "mortgage_discount_points_fee_fraction"
        ]
        self.house_appraisal_cost: float = kwargs["house_appraisal_cost"]
        self.credit_report_fee: float = kwargs["credit_report_fee"]
        self.transfer_tax_fraction: float = kwargs["transfer_tax_fraction"]
        self.seller_burden_of_transfer_tax_fraction: float = kwargs[
            "seller_burden_of_transfer_tax_fraction"
        ]
        self.recording_fee_fraction: float = kwargs["recording_fee_fraction"]
        self.annual_property_tax_rate: float = kwargs["annual_property_tax_rate"]
        self.realtor_commission_fraction: float = kwargs["realtor_commission_fraction"]
        self.hoa_transfer_fee: float = kwargs["hoa_transfer_fee"]
        self.seller_burden_of_hoa_transfer_fee: float = kwargs[
            "seller_burden_of_hoa_transfer_fee"
        ]
        self.house_inspection_cost: float = kwargs["house_inspection_cost"]
        self.pest_inspection_cost: float = kwargs["pest_inspection_cost"]
        self.escrow_fixed_fee: float = kwargs["escrow_fixed_fee"]
        self.flood_certification_fee: float = kwargs["flood_certification_fee"]
        self.title_search_fee: float = kwargs["title_search_fee"]
        self.seller_burden_of_title_search_fee_fraction: float = kwargs[
            "seller_burden_of_title_search_fee_fraction"
        ]
        self.attorney_fee: float = kwargs["attorney_fee"]
        self.closing_protection_letter_fee: float = kwargs[
            "closing_protection_letter_fee"
        ]
        self.search_abstract_fee: float = kwargs["search_abstract_fee"]
        self.survey_fee: float = kwargs["survey_fee"]
        self.notary_fee: float = kwargs["notary_fee"]
        self.deep_prep_fee: float = kwargs["deep_prep_fee"]
        self.lenders_title_insurance_fraction: float = kwargs[
            "lenders_title_insurance_fraction"
        ]
        self.owners_title_insurance_fraction: float = kwargs[
            "owners_title_insurance_fraction"
        ]
        self.endorsement_fees: float = kwargs["endorsement_fees"]
        self.annual_homeowners_insurance_fraction: float = kwargs[
            "annual_homeowners_insurance_fraction"
        ]
        self.monthly_utilities: float = kwargs["monthly_utilities"]
        self.annual_maintenance_cost_fraction: float = kwargs[
            "annual_maintenance_cost_fraction"
        ]
        self.monthly_hoa_fees: float = kwargs["monthly_hoa_fees"]
        self.annual_management_cost_fraction: float = kwargs[
            "annual_management_cost_fraction"
        ]
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any house configs are invalid
        """
        assert self.sale_price > 0, "House sale price must be positive."
        assert (
            self.down_payment_fraction >= 0 and self.down_payment_fraction <= 1
        ), "Down payment fraction must be between 0 and 1 inclusive."
        assert (
            self.mortgage_annual_interest_rate >= 0
        ), "Mortgage annual interest rate must be non-negative."
        assert (
            self.mortgage_term_months > 0
        ), "Mortgage term in months must be positive."
        assert self.pmi_fraction >= 0, "PMI fraction must be non-negative."
        assert (
            self.mortgage_origination_points_fee_fraction >= 0
        ), "Mortgage original points fee fraction must be non-negative."
        assert (
            self.mortgage_processing_fee >= 0
        ), "Mortgage processing fee must be non-negative."
        assert (
            self.mortgage_underwriting_fee >= 0
        ), "Mortgage underwriting fee must be non-negative."
        assert (
            self.mortgage_discount_points_fee_fraction >= 0
        ), "Mortgage discount points fee fraction must be non-negative."
        assert (
            self.house_appraisal_cost >= 0
        ), "House appraisal cost must be non-negative."
        assert self.credit_report_fee >= 0, "Credit report fee must be non-negative."
        assert (
            self.transfer_tax_fraction >= 0
        ), "Transfer tax fraction must be non-negative."
        assert (
            self.seller_burden_of_transfer_tax_fraction >= 0
            and self.seller_burden_of_transfer_tax_fraction <= 1
        ), "Seller burden fraction of transfer tax must be between 0 and 1 inclusive."
        assert (
            self.recording_fee_fraction >= 0
        ), "Recording fee fraction must be non-negative."
        assert (
            self.annual_property_tax_rate >= 0
        ), "Annual property tax rate must be non-negative."
        assert (
            self.realtor_commission_fraction >= 0
        ), "Realtor commission fraction must be non-negative."
        assert self.hoa_transfer_fee >= 0, "HOA transfer fee must be non-negative."
        assert (
            self.seller_burden_of_hoa_transfer_fee >= 0
            and self.seller_burden_of_hoa_transfer_fee <= 1
        ), "Seller burden fraction of HOA fee must be between 0 and 1 inclusive."
        assert (
            self.house_inspection_cost >= 0
        ), "House inspection cost must be non-negative."
        assert (
            self.pest_inspection_cost >= 0
        ), "Pest inspection cost must be non-negative."
        assert self.escrow_fixed_fee >= 0, "Escrow fixed fee must be non-negative."
        assert (
            self.flood_certification_fee >= 0
        ), "Flood certification fee must be non-negative."
        assert self.title_search_fee >= 0, "Title search fee must be non-negative."
        assert (
            self.seller_burden_of_title_search_fee_fraction >= 0
            and self.seller_burden_of_title_search_fee_fraction <= 1
        ), "Seller burden fraction of title search fee must be non-negative."
        assert self.attorney_fee >= 0, "Attorney fee must be non-negative."
        assert (
            self.closing_protection_letter_fee >= 0
        ), "Closing protection letter fee must be non-negative."
        assert (
            self.search_abstract_fee >= 0
        ), "Search abstract fee must be non-negative."
        assert self.survey_fee >= 0, "Survey fee must be non-negative."
        assert self.notary_fee >= 0, "Notary fee must be non-negative."
        assert self.deep_prep_fee >= 0, "Dead prep fee must be non-negative."
        assert (
            self.lenders_title_insurance_fraction >= 0
        ), "Lenders title insurance fraction must be non-negative"
        assert (
            self.owners_title_insurance_fraction >= 0
        ), "Owners title insurance fraction must be non-negative."
        assert self.endorsement_fees >= 0, "Endorsement fees must be non-negative."
        assert (
            self.annual_homeowners_insurance_fraction >= 0
        ), "Annual homeowners insurance fraction must be non-negative."
        assert self.monthly_utilities >= 0, "Monthly utilities must be non-negative."
        assert (
            self.annual_maintenance_cost_fraction >= 0
        ), "Annual maintenance cost fraction must be non-negative."
        assert self.monthly_hoa_fees >= 0, "Monthly HOA fees must be non-negative."
        assert (
            self.annual_management_cost_fraction >= 0
        ), "Annual management cost fraction must be non-negative."

    def get_down_payment(self):
        return self.down_payment_fraction * self.sale_price

    def get_initial_loan_amount(self):
        return (1 - self.down_payment_fraction) * self.sale_price

    def get_upfront_one_time_cost(self):
        return (
            self.mortgage_origination_points_fee_fraction
            * self.get_initial_loan_amount()
            + self.mortgage_processing_fee
            + self.mortgage_underwriting_fee
            + self.mortgage_discount_points_fee_fraction
            * self.get_initial_loan_amount()
            + self.house_appraisal_cost
            + self.credit_report_fee
            + (1 - self.seller_burden_of_transfer_tax_fraction)
            * self.transfer_tax_fraction
            * self.sale_price
            + (self.recording_fee_fraction * self.sale_price)
            + (self.realtor_commission_fraction * self.sale_price)
            + (1 - self.seller_burden_of_hoa_transfer_fee) * self.hoa_transfer_fee
            + self.house_inspection_cost
            + self.pest_inspection_cost
            + self.escrow_fixed_fee
            + self.flood_certification_fee
            + (1 - self.seller_burden_of_title_search_fee_fraction)
            * self.title_search_fee
            + self.attorney_fee
            + self.closing_protection_letter_fee
            + self.search_abstract_fee
            + self.survey_fee
            + self.notary_fee
            + self.deep_prep_fee
            + self.lenders_title_insurance_fraction * self.get_initial_loan_amount()
            + self.owners_title_insurance_fraction * self.get_initial_loan_amount()
            + self.endorsement_fees
        )

    def get_monthly_mortgage_payment(self):
        # https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:series/x9e81a4f98389efdf:geo-series-notation/v/geometric-series-sum-to-figure-out-mortgage-payments
        # NOTE mortgages typically use the annual rate divided by 12
        # as opposed to using the "equivalent" monthly compound rate
        i = self.mortgage_annual_interest_rate / 12
        r = 1 / (1 + i)
        L = self.get_initial_loan_amount()
        return round(L * (1 - r) / (r - r ** (self.mortgage_term_months + 1)), 2)

    def get_monthly_house_values(self, num_months: int):
        return math_utils.project_growth(
            principal=self.sale_price,
            annual_growth_rate=self.annual_assessed_value_inflation_rate,
            compound_monthly=True,
            num_months=num_months,
        )

    def get_house_value_related_monthly_costs(self, num_months: int) -> float:
        first_month_cost = self.sale_price * (
            self.annual_property_tax_rate / 12
            + self.annual_homeowners_insurance_fraction / 12
            + self.annual_maintenance_cost_fraction / 12
            + self.annual_management_cost_fraction / 12
        )
        return math_utils.project_growth(
            principal=first_month_cost,
            annual_growth_rate=self.annual_assessed_value_inflation_rate,
            compound_monthly=True,
            num_months=num_months,
        )

    def _get_first_inflation_related_monthly_cost(self) -> float:
        return self.monthly_utilities + self.monthly_hoa_fees

    def get_inflation_related_monthly_costs(
        self, annual_inflation_rate: float, num_months: int
    ) -> float:
        return math_utils.project_growth(
            principal=self._get_first_inflation_related_monthly_cost(),
            annual_growth_rate=annual_inflation_rate,
            compound_monthly=True,
            num_months=num_months,
        )
