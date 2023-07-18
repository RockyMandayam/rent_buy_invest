import yaml


class HouseConfig(yaml.YAMLObject):
    """Stores house config.

    Due to using yaml_tag = "!HouseConfig", the yaml library handles auto-
    converting from a yaml file to an instance of this class. Therefore,
    the __init__ method is not used.

    Documentation of the instance variable types:
    # TODO add documentation
    # TODO maybe just point to the yaml file
    """

    yaml_tag: str = "!HouseConfig"

    # __init__ method not used due to yaml.YAMLObject

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any house configs are invalid
        """
        assert self.sale_price > 0, "House sale price must be positive."
        assert self.down_payment_fraction >= 0 and self.down_payment_fraction <= 1, "Down payment fraction must be between 0 and 1 inclusive."
        assert self.mortgage_annual_interest_rate >= 0, "Mortgage annual interest rate must be non-negative."
        assert self.mortgage_term_months > 0, "Mortgage term in months must be positive."
        assert self.pmi_fraction >= 0, "PMI fraction must be non-negative."
        assert self.mortgage_origination_points_fee >= 0, "Mortgage original points fee must be non-negative."
        assert self.mortgage_processing_fee >= 0, "Mortgage processing fee must be non-negative."
        assert self.mortgage_underwriting_fee >= 0, "Mortgage underwriting fee must be non-negative."
        assert self.mortgage_discount_points_fee >= 0, "Mortgage discount points fee must be non-negative."
        assert self.house_appraisal_cost >= 0, "House appraisal cost must be non-negative."
        assert self.credit_report_fee >= 0, "Credit report fee must be non-negative."
        assert self.transfer_tax_fraction >= 0, "Transfer tax fraction must be non-negative."
        assert (
            self.seller_burden_of_transfer_tax_fraction >= 0
            and self.seller_burden_of_transfer_tax_fraction <= 1
        ), "Seller burden fraction of transfer tax must be between 0 and 1 inclusive."
        assert self.recording_fee_fraction >= 0, "Recording fee fraction must be non-negative."
        assert self.monthly_property_tax_rate >= 0, "Monthly property tax rate must be non-negative."
        assert self.realtor_commission_fraction >= 0, "Realtor commission fraction must be non-negative."
        assert self.hoa_transfer_fee >= 0, "HOA transfer fee must be non-negative."
        assert (
            self.seller_burden_of_hoa_transfer_fee >= 0
            and self.seller_burden_of_hoa_transfer_fee <= 1
        ), "Seller burden fraction of HOA fee must be between 0 and 1 inclusive."
        assert self.house_inspection_cost >= 0, "House inspection cost must be non-negative."
        assert self.pest_inspection_cost >= 0, "Pest inspection cost must be non-negative."
        assert self.escrow_fixed_fee >= 0, "Escrow fixed fee must be non-negative."
        assert self.flood_certification_fee >= 0, "Flood certification fee must be non-negative."
        assert self.title_search_fee >= 0, "Title search fee must be non-negative."
        assert (
            self.seller_burden_of_title_search_fee_fraction >= 0
            and self.seller_burden_of_title_search_fee_fraction <= 1
        ), "Seller burden fraction of title search fee must be non-negative."
        assert self.attorney_fee >= 0, "Attorney fee must be non-negative."
        assert self.closing_protection_letter_fee >= 0, "Closing protection letter fee must be non-negative."
        assert self.search_abstract_fee >= 0, "Search abstract fee must be non-negative."
        assert self.survey_fee >= 0, "Survey fee must be non-negative."
        assert self.notary_fee >= 0, "Notary fee must be non-negative."
        assert self.deep_prep_fee >= 0, "Dead prep fee must be non-negative."
        assert self.lenders_title_insurance_fraction >= 0, "Lenders title insurance fraction must be non-negative"
        assert self.owners_title_insurance_fraction >= 0, "Owners title insurance fraction must be non-negative."
        assert self.endorsement_fees >= 0, "Endorsement fees must be non-negative."
        assert self.monthly_homeowners_insurance_fraction >= 0, "Monthly homeowners insurance fraction must be non-negative."
        assert self.monthly_utilities >= 0, "Monthly utilities must be non-negative."
        assert self.annual_maintenance_cost_fraction >= 0, "Annual maintenance cost fraction must be non-negative."
        assert self.monthly_hoa_fees >= 0, "Monthly HOA fees must be non-negative."
        assert self.annual_management_cost_fraction >= 0, "Annual management cost fraction must be non-negative."

    def get_down_payment(self):
        return self.down_payment_fraction * self.sale_price

    def get_loan_amount(self):
        return (1 - self.down_payment_fraction) * self.sale_price

    def get_monthly_mortgage_payment(self):
        # https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:series/x9e81a4f98389efdf:geo-series-notation/v/geometric-series-sum-to-figure-out-mortgage-payments
        # NOTE mortgages typically use the annual rate divided by 12
        # as opposed to using the "equivalnt" monthly compound rate
        i = self.mortgage_annual_interest_rate / 12
        r = 1 / (1 + i)
        L = self.get_loan_amount()
        return L * (1 - r) / (r - r ** (self.mortgage_term_months + 1))

    def get_upfront_one_time_cost(self):
        return (
            self.mortgage_origination_points_fee
            + self.mortgage_processing_fee
            + self.mortgage_underwriting_fee
            + self.mortgage_discount_points_fee
            + self.house_appraisal_cost
            + self.credit_report_fe
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
            + self.lenders_title_insurance_fraction * self.get_loan_amount()
            + self.owners_title_insurance_fraction * self.get_loan_amount()
            + self.endorsement_fees
        )

    # TODO test this and all parse methods
    @staticmethod
    def parse_house_config() -> "HouseConfig":
        """Load house config yaml file as an instance of this class

        Raises:
            AssertionError: If any house configs are invalid
        """
        # TODO replace this absolute path string literal
        with open(
            "/Users/rocky/Downloads/rent_buy_invest/configs/house-config.yaml"
        ) as f:
            house_config = yaml.load(f)
        house_config._validate()
        return house_config


if __name__ == "__main__":
    print("Parsing house config")
    c = HouseConfig.parse_house_config()
    print(c)
    print("Done parsing house config")
