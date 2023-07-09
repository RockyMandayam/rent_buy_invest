import yaml


class RentConfig(yaml.YAMLObject):
	"""Stores rent config.

	Due to using yaml_tag = "!RentConfig", the yaml library handles auto-
	converting from a yaml file to an instance of this class. Therefore,
	the __init__ method is not used.

	Documentation of the instance variable types:
		self.monthly_rent (float): Monthly rent for first month
		self.monthly_utilities (float): Monthly utilities for the first month
		self.monthly_renters_insurance (float): Monthly renters insurance for
			the first month
		self.monthly_parking_fee (float): Monthly parking fee
		self.annual_rent_inflation (float): ANNUAL rent inflation rate. This
			will be applied to all rent-related expenses.E.g., not just rent
			but also utilities, etc.
		self.inflation_adjustment_period (int): How often (in months) to update
			rent-related expenses for inflation. If you rent with 12-month
			leases, 12 is a good number here.
	"""

	yaml_tag: str = "!RentConfig"

	# __init__ method not used due to yaml.YAMLObject

	def _validate(self) -> None:
		"""Sanity checks the configs.

		Raises:
			AssertionError: If any rent configs are invalid
		"""
		assert self.monthly_rent >= 0
		assert self.monthly_utilities >= 0
		assert self.monthly_renters_insurance >= 0
		assert self.monthly_parking_fee >= 0
		assert self.inflation_adjustment_period >= 1

	@staticmethod
	def parse_rent_config() -> 'RentConfig':
		"""Load rent config yaml file as an instance of this class
		
		Raises:
			AssertionError: If any rent configs are invalid
		"""
		# TODO replace this absolute path string literal
		with open("/Users/rocky/Downloads/rent_buy_invest/configs/rent-config.yaml") as f:
			rent_config = yaml.load(f)
		rent_config._validate()
		return rent_config


if __name__ == "__main__":
	print("Parsing rent config")
	c = RentConfig.parse_rent_config()
	print(c)
	print(c.__dict__)
	print("Done parsing rent config")
