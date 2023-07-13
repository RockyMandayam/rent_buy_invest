import yaml

from ..utils import math_utils

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
		assert self.sale_price > 0
		assert self.down_payment_fraction >= 0 and down_payment_fraction <= 1
		assert self.mortgage_annual_interest_rate >= 0
		assert self.mortgage_term_months > 0
		assert self.pmi_fraction >= 0
		assert self.mortgage_origination_points_fee >= 0
		assert self.mortgage_processing_fee >= 0
		assert self.mortgage_underwriting_fee >= 0
		assert self.mortgage_discount_points_fee >= 0
		assert self.house_appraisal_cost >= 0
		assert self.credit_report_fee >= 0
		assert self.transfer_tax_fraction >= 0
		assert self.seller_burden_of_transfer_tax_fraction >= 0 and self.seller_burden_of_transfer_tax_fraction <= 1
		assert self.recording_fee_fraction >= 0
		assert self.monthly_property_tax_rate >= 0
		assert self.realtor_commission_fraction >= 0
		assert self.hoa_transfer_fee >= 0
		assert self.seller_burden_of_hoa_transfer_fee >= 0 and self.seller_burden_of_hoa_transfer_fee <= 1
		assert self.house_inspection_cost >= 0
		assert self.pest_inspection_cost >= 0
		assert self.escrow_fixed_fee >= 0
		assert self.flood_certification_fee >= 0
		assert self.title_search_fee >= 0
		assert self.seller_burden_of_title_search_fee_fraction >= 0 and self.seller_burden_of_title_search_fee_fraction <= 1
		assert self.attorney_fee >= 0
		assert self.closing_protection_letter_fee >= 0
		assert self.search_abstract_fee >= 0
		assert self.survey_fee >= 0
		assert self.notary_fee >= 0
		assert self.deep_prep_fee >= 0
		assert self.lenders_title_insurance_fraction >= 0
		assert self.owners_title_insurance_fraction >= 0
		assert self.endorsement_fees >= 0
		assert self.monthly_homeowners_insurance_fraction >= 0
		assert self.monthly_utilities >= 0
		assert self.annual_maintenance_cost_fraction >= 0
		assert self.monthly_hoa_fees >= 0
		assert self.annual_management_cost_fraction >= 0

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
		return L * (1 - r) / (r - r**(n+1))

	def get_upfront_one_time_cost(self):
		return self.mortgage_origination_points_fee
			+ self.mortgage_processing_fee
			+ self.mortgage_underwriting_fee
			+ self.mortgage_discount_points_fee
			+ self.house_appraisal_cost
			+ self.credit_report_fe
			+ (1 - self.seller_burden_of_transfer_tax_fraction) * self.transfer_tax_fraction * self.sale_price
			+ (self.recording_fee_fraction * self.sale_price)
			+ (self.realtor_commission_fraction * self.sale_price)
			+ (1 - self.seller_burden_of_hoa_transfer_fee) * self.hoa_transfer_fee
			+ self.house_inspection_cost
			+ self.pest_inspection_cost
			+ self.escrow_fixed_fee
			+ self.flood_certification_fee
			+ (1 - self.seller_burden_of_title_search_fee_fraction) * self.title_search_fee
			+ self.attorney_fee
			+ self.closing_protection_letter_fee
			+ self.search_abstract_fee
			+ self.survey_fee
			+ self.notary_fee
			+ self.deep_prep_fee
			+ self.lenders_title_insurance_fraction * self.get_loan_amount()
			+ self.owners_title_insurance_fraction * self.get_loan_amount()
			+ self.endorsement_fees
	
	# TODO test this and all parse methods
	@staticmethod
	def parse_house_config() -> 'HouseConfig':
		"""Load house config yaml file as an instance of this class
		
		Raises:
			AssertionError: If any house configs are invalid
		"""
		# TODO replace this absolute path string literal
		with open("/Users/rocky/Downloads/rent_buy_invest/configs/house-config.yaml") as f:
			house_config = yaml.load(f)
		house_config._validate()
		return house_config


if __name__ == "__main__":
	print("Parsing house config")
	c = HouseConfig.parse_house_config()
	print(c)
	print("Done parsing house config")
