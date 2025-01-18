import math
from typing import Any

from rent_buy_invest.configs.config import Config
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR, project_growth


class BuyConfig(Config):
    """Stores buy config.

    Class Attributes:
        schema_path (str): Buy config schema path

    Instance Attributes:
        See rent_buy_invest/configs/schemas/buy-config-schema.md for documentation
    """

    MAX_ANNUAL_RENT_INFLATION_RATE = 1.0
    MAX_MORTGAGE_ANNUAL_INTEREST_RATE = 1.0
    MAX_MORTGAGE_TERM = 60 * MONTHS_PER_YEAR
    MAX_UPFRONT_MORTGAGE_INSURANCE_FRACTION = 0.1
    MAX_ANNUAL_MORTGAGE_INSURANCE_FRACTION = 0.05
    MAX_MORTGAGE_ORIGINATION_POINTS_FEE_FRACTION = 0.1
    MAX_MORTGAGE_PROCESSING_FEE = 1000.0
    MAX_MORTGAGE_UNDERWRITING_FEE = 1000.0
    MAX_MORTGAGE_DISCOUNT_POINTS_FEE_FRACTION = 0.05
    MAX_HOME_APPRAISAL_COST = 5000.0
    MAX_CREDIT_REPORT_FEE = 500.0
    MAX_TRANSFER_TAX_FRACTION = 0.01
    MAX_RECORDING_FEE_FRACTION = 0.1
    MAX_ANNUAL_PROPERTY_TAX_RATE = 0.1
    MAX_REALTOR_COMMISSION_FRACTION = 0.1
    MAX_HOA_TRANSFER_FEE = 5000.0
    MAX_HOME_INSPECTION_COST = 5000.0
    MAX_PEST_INSPECTION_COST = 5000.0
    MAX_ESCROW_FIXED_FEE = 5000.0
    MAX_FLOOD_CERTIFICATION_FEE = 1000.0
    MAX_TITLE_SEARCH_FEE = 1000.0
    MAX_ATTORNEY_FEE = 10000.0
    MAX_CLOSING_PROTECTION_LETTER_FEE = 500.0
    MAX_SEARCH_ABSTRACT_FEE = 5000.0
    MAX_SURVEY_FEE = 5000.0
    MAX_NOTARY_FEE = 2000.0
    MAX_DEED_PREP_FEE = 1000.0
    MAX_ENDORSEMENT_FEES = 1000
    MAX_ANNUAL_HOMEOWNERS_INSURANCE_FRACTION = 0.05
    MAX_MONTHLY_UTILITIES = 1000.0
    MAX_ANNUAL_MAINTENANCE_COST_FRACTION = 0.05
    MAX_MONTHLY_HOA_FEES = 1000.0
    MAX_ANNUAL_MANAGEMENT_COST_FRACTION = 0.05
    # TODO add upper limit for monthly_rental_income
    MAX_MONTHLY_RENTAL_INCOME_INFLATION_RATE = 0.3
    MAX_UPFRONT_ONE_TIME_COST_AS_FRACTION_OF_SALE_PRICE = 0.5

    class RentalIncomeConfig:
        def __init__(
            self,
            annual_management_cost_fraction: float,
            # TODO do type checking for all args like this
            rental_income_waiting_period_months: int,
            monthly_rental_income: float,
            rental_income_annual_inflation_rate: float,
            occupancy_rate: float,
        ) -> None:
            self.annual_management_cost_fraction = annual_management_cost_fraction
            self.rental_income_waiting_period_months = (
                rental_income_waiting_period_months
            )
            self.monthly_rental_income = monthly_rental_income
            self.rental_income_annual_inflation_rate = (
                rental_income_annual_inflation_rate
            )
            self.occupancy_rate = occupancy_rate
            self._validate()

        def _validate(self) -> None:
            # TODO this is duplicate code, feels wrong...
            for attribute, value in self.__dict__.items():
                assert math.isfinite(
                    value
                ), f"'{attribute}' attribute must not be NaN, infinity, or negative infinity."
            assert (
                self.annual_management_cost_fraction >= 0
            ), "Annual management cost fraction must be non-negative."
            assert (
                self.rental_income_waiting_period_months >= 0
            ), "rental_income_waiting_period_months must be non-negative."
            assert (
                self.monthly_rental_income >= 0
            ), "monthly_rental_income must be non-negative."
            assert (
                self.occupancy_rate >= 0 and self.occupancy_rate <= 1
            ), "occupancy_rate must be between 0 and 1 inclusive."
            # TODO can't access _validate_max_value since that is in Config class and RentalIncomeConfig
            # doesn't inherit from Config. RentalIncomeConfig could inherit from Config, but then specifying
            # the schema is tricky. For now, I'm just "ad hoc" checking these fields instead of calling
            # _validate_max_value
            for attr_name, max_value in (
                (
                    "annual_management_cost_fraction",
                    BuyConfig.MAX_ANNUAL_MANAGEMENT_COST_FRACTION,
                ),
                (
                    "rental_income_annual_inflation_rate",
                    BuyConfig.MAX_MONTHLY_RENTAL_INCOME_INFLATION_RATE,
                ),
            ):
                attr_val = getattr(self, attr_name)
                assert (
                    attr_val <= max_value
                ), f"Please set '{attr_name}' to something reasonable (at most {max_value})"

    @classmethod
    def schema_path(cls) -> str:
        return "rent_buy_invest/configs/schemas/buy-config-schema.json"

    def __init__(
        self,
        **kwargs: dict[str, Any],  # lots of parameters, see body of this method
    ) -> None:
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in Config.
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
        self.upfront_mortgage_insurance_fraction: float = kwargs[
            "upfront_mortgage_insurance_fraction"
        ]
        self.annual_mortgage_insurance_fraction: float = kwargs[
            "annual_mortgage_insurance_fraction"
        ]
        self.is_fha_loan: bool = kwargs["is_fha_loan"]
        self.mortgage_origination_points_fee_fraction: float = kwargs[
            "mortgage_origination_points_fee_fraction"
        ]
        self.mortgage_processing_fee: float = kwargs["mortgage_processing_fee"]
        self.mortgage_underwriting_fee: float = kwargs["mortgage_underwriting_fee"]
        self.mortgage_discount_points_fee_fraction: float = kwargs[
            "mortgage_discount_points_fee_fraction"
        ]
        self.home_appraisal_cost: float = kwargs["home_appraisal_cost"]
        self.credit_report_fee: float = kwargs["credit_report_fee"]
        self.flood_certification_fee: float = kwargs["flood_certification_fee"]
        self.transfer_tax_fraction: float = kwargs["transfer_tax_fraction"]
        self.seller_burden_of_transfer_tax_fraction: float = kwargs[
            "seller_burden_of_transfer_tax_fraction"
        ]
        self.recording_fee_fraction: float = kwargs["recording_fee_fraction"]
        self.annual_property_tax_rate: float = kwargs["annual_property_tax_rate"]
        self.buyer_realtor_commission_fraction: float = kwargs[
            "buyer_realtor_commission_fraction"
        ]
        self.seller_realtor_commission_fraction: float = kwargs[
            "seller_realtor_commission_fraction"
        ]
        self.hoa_transfer_fee: float = kwargs["hoa_transfer_fee"]
        self.seller_burden_of_hoa_transfer_fee: float = kwargs[
            "seller_burden_of_hoa_transfer_fee"
        ]
        self.home_inspection_cost: float = kwargs["home_inspection_cost"]
        self.pest_inspection_cost: float = kwargs["pest_inspection_cost"]
        self.escrow_fixed_fee: float = kwargs["escrow_fixed_fee"]
        self.seller_burden_of_escrow_fixed_fee: float = kwargs[
            "seller_burden_of_escrow_fixed_fee"
        ]
        self.title_search_fee: float = kwargs["title_search_fee"]
        self.seller_burden_of_title_search_fee_fraction: float = kwargs[
            "seller_burden_of_title_search_fee_fraction"
        ]
        self.buyer_attorney_fee: float = kwargs["buyer_attorney_fee"]
        self.seller_attorney_fee: float = kwargs["seller_attorney_fee"]
        self.closing_protection_letter_fee: float = kwargs[
            "closing_protection_letter_fee"
        ]
        self.search_abstract_fee: float = kwargs["search_abstract_fee"]
        self.survey_fee: float = kwargs["survey_fee"]
        self.notary_fee: float = kwargs["notary_fee"]
        self.deed_prep_fee: float = kwargs["deed_prep_fee"]
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
        # TODO this seems wrong
        rental_income_config_kwargs = kwargs["rental_income_config"]
        if rental_income_config_kwargs:
            self.rental_income_config = BuyConfig.RentalIncomeConfig(
                rental_income_config_kwargs["annual_management_cost_fraction"],
                rental_income_config_kwargs["rental_income_waiting_period_months"],
                rental_income_config_kwargs["monthly_rental_income"],
                rental_income_config_kwargs["rental_income_annual_inflation_rate"],
                rental_income_config_kwargs["occupancy_rate"],
            )
        else:
            self.rental_income_config = None
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any buy config fields are invalid
        """
        for attribute, value in self.__dict__.items():
            # TODO this feels wrong
            if attribute == "rental_income_config":
                continue
            assert math.isfinite(
                value
            ), f"'{attribute}' attribute must not be NaN, infinity, or negative infinity."
        assert self.sale_price > 0, "Home sale price must be positive."
        assert (
            self.down_payment_fraction >= 0 and self.down_payment_fraction <= 1
        ), "Down payment fraction must be between 0 and 1 inclusive."
        assert (
            self.mortgage_annual_interest_rate >= 0
        ), "Mortgage annual interest rate must be non-negative."
        assert (
            self.mortgage_term_months > 0
        ), "Mortgage term in months must be positive."
        assert (
            self.upfront_mortgage_insurance_fraction >= 0
        ), "Upfront mortgage insurance fraction must be non-negative."
        assert (
            self.annual_mortgage_insurance_fraction >= 0
        ), "Annual mortgage insurance fraction must be non-negative."
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
            self.home_appraisal_cost >= 0
        ), "Home appraisal cost must be non-negative."
        assert self.credit_report_fee >= 0, "Credit report fee must be non-negative."
        assert (
            self.flood_certification_fee >= 0
        ), "Flood certification fee must be non-negative."
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
            self.buyer_realtor_commission_fraction >= 0
        ), "Buyer ealtor commission fraction must be non-negative."
        assert (
            self.seller_realtor_commission_fraction >= 0
        ), "Seller realtor commission fraction must be non-negative."
        assert self.hoa_transfer_fee >= 0, "HOA transfer fee must be non-negative."
        assert (
            self.seller_burden_of_hoa_transfer_fee >= 0
            and self.seller_burden_of_hoa_transfer_fee <= 1
        ), "Seller burden fraction of HOA fee must be between 0 and 1 inclusive."
        assert (
            self.home_inspection_cost >= 0
        ), "Home inspection cost must be non-negative."
        assert (
            self.pest_inspection_cost >= 0
        ), "Pest inspection cost must be non-negative."
        assert self.escrow_fixed_fee >= 0, "Escrow fixed fee must be non-negative."
        assert (
            self.seller_burden_of_escrow_fixed_fee >= 0
            and self.seller_burden_of_escrow_fixed_fee <= 1
        ), "seller_burden_of_escrow_fixed_fee must be between 0 and 1 inclusve."
        assert self.title_search_fee >= 0, "Title search fee must be non-negative."
        assert (
            self.seller_burden_of_title_search_fee_fraction >= 0
            and self.seller_burden_of_title_search_fee_fraction <= 1
        ), "Seller burden fraction of title search fee must be between 0 and 1 inclusive"
        assert self.buyer_attorney_fee >= 0, "Attorney fee must be non-negative."
        assert self.seller_attorney_fee >= 0, "Attorney fee must be non-negative."
        assert (
            self.closing_protection_letter_fee >= 0
        ), "Closing protection letter fee must be non-negative."
        assert (
            self.search_abstract_fee >= 0
        ), "Search abstract fee must be non-negative."
        assert self.survey_fee >= 0, "Survey fee must be non-negative."
        assert self.notary_fee >= 0, "Notary fee must be non-negative."
        assert self.deed_prep_fee >= 0, "Dead prep fee must be non-negative."
        assert (
            self.lenders_title_insurance_fraction >= 0
            and self.lenders_title_insurance_fraction <= 1
        ), "Lenders title insurance fraction must be between 0 and 1 inclusive."
        assert (
            self.owners_title_insurance_fraction >= 0
            and self.owners_title_insurance_fraction <= 1
        ), "Owners title insurance fraction must be between 0 and 1 inclusive."
        assert self.endorsement_fees >= 0, "Endorsement fees must be non-negative."
        assert (
            self.annual_homeowners_insurance_fraction >= 0
        ), "Annual homeowners insurance fraction must be non-negative."
        assert self.monthly_utilities >= 0, "Monthly utilities must be non-negative."
        assert (
            self.annual_maintenance_cost_fraction >= 0
        ), "Annual maintenance cost fraction must be non-negative."
        assert self.monthly_hoa_fees >= 0, "Monthly HOA fees must be non-negative."
        self._validate_max_value(
            "annual_assessed_value_inflation_rate",
            BuyConfig.MAX_ANNUAL_RENT_INFLATION_RATE,
        )
        self._validate_max_value(
            "mortgage_annual_interest_rate",
            BuyConfig.MAX_MORTGAGE_ANNUAL_INTEREST_RATE,
        )
        self._validate_max_value("mortgage_term_months", BuyConfig.MAX_MORTGAGE_TERM)
        if self.initial_loan_amount:
            self._validate_max_value_as_fraction(
                "upfront_mortgage_insurance_fraction",
                "initial_loan_amount",
                BuyConfig.MAX_UPFRONT_MORTGAGE_INSURANCE_FRACTION,
            )
            self._validate_max_value_as_fraction(
                "annual_mortgage_insurance_fraction",
                "initial_loan_amount",
                BuyConfig.MAX_ANNUAL_MORTGAGE_INSURANCE_FRACTION,
            )
            self._validate_max_value_as_fraction(
                "mortgage_origination_points_fee_fraction",
                "initial_loan_amount",
                BuyConfig.MAX_MORTGAGE_ORIGINATION_POINTS_FEE_FRACTION,
            )
        self._validate_max_value(
            "mortgage_processing_fee", BuyConfig.MAX_MORTGAGE_PROCESSING_FEE
        )
        self._validate_max_value(
            "mortgage_underwriting_fee", BuyConfig.MAX_MORTGAGE_UNDERWRITING_FEE
        )
        if self.initial_loan_amount:
            self._validate_max_value_as_fraction(
                "mortgage_discount_points_fee_fraction",
                "initial_loan_amount",
                BuyConfig.MAX_MORTGAGE_DISCOUNT_POINTS_FEE_FRACTION,
            )
        self._validate_max_value(
            "home_appraisal_cost", BuyConfig.MAX_HOME_APPRAISAL_COST
        )
        self._validate_max_value("credit_report_fee", BuyConfig.MAX_CREDIT_REPORT_FEE)
        self._validate_max_value(
            "flood_certification_fee", BuyConfig.MAX_FLOOD_CERTIFICATION_FEE
        )
        self._validate_max_value(
            "transfer_tax_fraction", BuyConfig.MAX_TRANSFER_TAX_FRACTION
        )
        self._validate_max_value(
            "recording_fee_fraction",
            BuyConfig.MAX_RECORDING_FEE_FRACTION,
        )
        self._validate_max_value(
            "annual_property_tax_rate", BuyConfig.MAX_ANNUAL_PROPERTY_TAX_RATE
        )
        self._validate_max_value(
            "buyer_realtor_commission_fraction",
            BuyConfig.MAX_REALTOR_COMMISSION_FRACTION,
        )
        self._validate_max_value(
            "seller_realtor_commission_fraction",
            BuyConfig.MAX_REALTOR_COMMISSION_FRACTION,
        )
        self._validate_max_value("hoa_transfer_fee", BuyConfig.MAX_HOA_TRANSFER_FEE)
        self._validate_max_value(
            "home_inspection_cost", BuyConfig.MAX_HOME_INSPECTION_COST
        )
        self._validate_max_value(
            "pest_inspection_cost", BuyConfig.MAX_PEST_INSPECTION_COST
        )
        self._validate_max_value("escrow_fixed_fee", BuyConfig.MAX_ESCROW_FIXED_FEE)
        self._validate_max_value("title_search_fee", BuyConfig.MAX_TITLE_SEARCH_FEE)
        self._validate_max_value("buyer_attorney_fee", BuyConfig.MAX_ATTORNEY_FEE)
        self._validate_max_value("seller_attorney_fee", BuyConfig.MAX_ATTORNEY_FEE)
        self._validate_max_value(
            "closing_protection_letter_fee",
            BuyConfig.MAX_CLOSING_PROTECTION_LETTER_FEE,
        )
        self._validate_max_value(
            "search_abstract_fee", BuyConfig.MAX_SEARCH_ABSTRACT_FEE
        )
        self._validate_max_value("survey_fee", BuyConfig.MAX_SURVEY_FEE)
        self._validate_max_value("notary_fee", BuyConfig.MAX_NOTARY_FEE)
        self._validate_max_value("deed_prep_fee", BuyConfig.MAX_DEED_PREP_FEE)
        self._validate_max_value("endorsement_fees", BuyConfig.MAX_ENDORSEMENT_FEES)
        self._validate_max_value(
            "annual_homeowners_insurance_fraction",
            BuyConfig.MAX_ANNUAL_HOMEOWNERS_INSURANCE_FRACTION,
        )
        self._validate_max_value("monthly_utilities", BuyConfig.MAX_MONTHLY_UTILITIES)
        self._validate_max_value(
            "annual_maintenance_cost_fraction",
            BuyConfig.MAX_ANNUAL_MAINTENANCE_COST_FRACTION,
        )
        self._validate_max_value("monthly_hoa_fees", BuyConfig.MAX_MONTHLY_HOA_FEES)

        assert (
            self.get_upfront_one_time_cost()
            <= BuyConfig.MAX_UPFRONT_ONE_TIME_COST_AS_FRACTION_OF_SALE_PRICE
            * self.sale_price
        ), f"Please check the buy config for unreasonably high values and make sure the upfront one time cost adds up to something reasonable (at most {BuyConfig.MAX_UPFRONT_ONE_TIME_COST_AS_FRACTION_OF_SALE_PRICE} of the sale price)"

    @property
    def initial_loan_fraction(self):
        """This is also known as the loan-to-purchase-price (LTPP)"""
        return 1 - self.down_payment_fraction

    @property
    def down_payment(self):
        return self.down_payment_fraction * self.sale_price

    @property
    def initial_loan_amount(self):
        return self.initial_loan_fraction * self.sale_price

    def get_upfront_one_time_cost(self):
        return (
            # fmt: off
            self.mortgage_origination_points_fee_fraction
                * self.initial_loan_amount
            # fmt: on
            + self.mortgage_processing_fee
            + self.mortgage_underwriting_fee
            # fmt: off
            + self.mortgage_discount_points_fee_fraction
                * self.initial_loan_amount
            # fmt: on
            + self.home_appraisal_cost
            + self.credit_report_fee
            + self.flood_certification_fee
            # fmt: off
            + (1 - self.seller_burden_of_transfer_tax_fraction)
                * self.transfer_tax_fraction
                * self.sale_price
            # fmt: on
            + (self.recording_fee_fraction * self.sale_price)
            + (self.buyer_realtor_commission_fraction * self.sale_price)
            + (1 - self.seller_burden_of_hoa_transfer_fee) * self.hoa_transfer_fee
            + self.home_inspection_cost
            + self.pest_inspection_cost
            + (1 - self.seller_burden_of_escrow_fixed_fee) * self.escrow_fixed_fee
            # fmt: off
            + (1 - self.seller_burden_of_title_search_fee_fraction)
                * self.title_search_fee
            # fmt: on
            + self.buyer_attorney_fee
            + self.closing_protection_letter_fee
            + self.search_abstract_fee
            + self.survey_fee
            + self.notary_fee
            + self.deed_prep_fee
            + self.lenders_title_insurance_fraction * self.initial_loan_amount
            + self.owners_title_insurance_fraction * self.initial_loan_amount
            + self.endorsement_fees
        )

    def get_monthly_mortgage_payment(self):
        # https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:series/x9e81a4f98389efdf:geo-series-notation/v/geometric-series-sum-to-figure-out-mortgage-payments
        # NOTE mortgages typically use the annual rate divided by MONTHS_PER_YEAR
        # as opposed to using the "equivalent" monthly compound rate
        i = self.mortgage_annual_interest_rate / MONTHS_PER_YEAR
        r = 1 / (1 + i)
        L = self.initial_loan_amount
        return round(L * (1 - r) / (r - r ** (self.mortgage_term_months + 1)), 2)

    def get_monthly_home_values(self, num_months: int):
        return project_growth(
            principal=self.sale_price,
            annual_growth_rate=self.annual_assessed_value_inflation_rate,
            compound_monthly=True,
            num_months=num_months,
        )

    def _get_first_home_value_related_monthly_costs(self) -> float:
        management_cost_fraction = (
            self.rental_income_config.annual_management_cost_fraction
            if self.rental_income_config
            else 0
        )
        return (
            self.sale_price
            * (
                self.annual_property_tax_rate
                + self.annual_maintenance_cost_fraction
                + management_cost_fraction
            )
            / MONTHS_PER_YEAR
        )

    def get_home_value_related_monthly_costs(self, num_months: int) -> float:
        return project_growth(
            principal=self._get_first_home_value_related_monthly_costs(),
            annual_growth_rate=self.annual_assessed_value_inflation_rate,
            compound_monthly=False,
            num_months=num_months,
        )

    def _get_first_inflation_related_monthly_cost(self) -> float:
        return (
            self.monthly_utilities
            + self.monthly_hoa_fees
            + self.sale_price
            * self.annual_homeowners_insurance_fraction
            / MONTHS_PER_YEAR
        )

    def get_inflation_related_monthly_costs(
        self, annual_inflation_rate: float, num_months: int
    ) -> list[float]:
        return project_growth(
            principal=self._get_first_inflation_related_monthly_cost(),
            annual_growth_rate=annual_inflation_rate,
            compound_monthly=False,
            num_months=num_months,
        )

    def get_monthly_rental_incomes(self, num_months: int) -> list[float]:
        if self.rental_income_config.rental_income_waiting_period_months >= num_months:
            return [0 for _ in range(self.num_months)]
        period_of_no_rental_income = [
            0
            for _ in range(
                self.rental_income_config.rental_income_waiting_period_months
            )
        ]
        if self.rental_income_config.rental_income_waiting_period_months == 0:
            first_month_rent_after_waiting = (
                self.rental_income_config.monthly_rental_income
            )
        else:
            first_month_rent_after_waiting = project_growth(
                principal=self.rental_income_config.monthly_rental_income,
                annual_growth_rate=self.rental_income_config.rental_income_annual_inflation_rate,
                # I want the most up-to-date rental price even if it doesn't coincide with a year boundary
                compound_monthly=True,
                num_months=self.rental_income_config.rental_income_waiting_period_months,
            )[-1]
        first_month_rent_after_waiting *= self.rental_income_config.occupancy_rate
        period_of_rental_income = project_growth(
            principal=first_month_rent_after_waiting,
            annual_growth_rate=self.rental_income_config.rental_income_annual_inflation_rate,
            compound_monthly=False,
            num_months=(
                num_months
                - self.rental_income_config.rental_income_waiting_period_months
            ),
        )
        return period_of_no_rental_income + period_of_rental_income
