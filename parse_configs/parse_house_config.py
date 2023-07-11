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
		assert sale_price > 0
		assert down_payment_fraction >= 0 and down_payment_fraction <= 1
		assert mortgage_annual_interest_rate >= 0
		assert mortgage_term_months > 0
		assert pmi_fraction >= 0
		assert mortgage_origination_points_fee >= 0
		assert mortgage_processing_fee >= 0
		assert mortgage_underwriting_fee >= 0
		assert mortgage_discount_points_fee >= 0
		assert house_appraisal_cost >= 0
		assert credit_report_fee >= 0
		assert transfer_tax_fraction >= 0
		assert seller_burden_of_transfer_tax_fraction >= 0 and seller_burden_of_transfer_tax_fraction <= 1
		assert recording_fee_fraction >= 0
		assert monthly_property_tax_rate >= 0
		assert realtor_commission_fraction >= 0
		assert hoa_transfer_fee >= 0
		assert seller_burden_of_hoa_transfer_fee >= 0 and seller_burden_of_hoa_transfer_fee <= 1
		assert house_inspection_cost >= 0
		assert pest_inspection_cost >= 0
		assert escrow_fixed_fee >= 0
		assert flood_certification_fee >= 0
		assert title_search_fee >= 0
		assert seller_burden_of_title_search_fee_fraction >= 0 and seller_burden_of_title_search_fee_fraction <= 1
		assert attorney_fee >= 0
		assert closing_protection_letter_fee >= 0
		assert search_abstract_fee >= 0
		assert survey_fee >= 0
		assert notary_fee >= 0
		assert deep_prep_fee >= 0
		assert lenders_title_insurance_fraction >= 0
		assert owners_title_insurance_fraction >= 0
		assert endorsement_fees >= 0
		assert monthly_homeowners_insurance_fraction >= 0
		assert monthly_utilities >= 0
		assert annual_maintenance_cost_fraction >= 0
		assert monthly_hoa_fees >= 0
		assert annual_management_cost_fraction >= 0

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
