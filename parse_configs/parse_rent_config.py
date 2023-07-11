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
		self.annual_rent_inflation_rate (float): ANNUAL rent inflation rate.
			This will be applied to all rent-related expenses.E.g., not just
			rent but also utilities, etc.
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

	def _get_total_monthly_cost(self) -> float:
		""" Get total monthly cost of renting for the first month """
		return self.monthly_rent + self.monthly_utilities + self.monthly_renters_insurance + self.monthly_parking_fee

	def get_monthly_costs_of_renting(self, num_months: int) -> float:
		"""Return the monthly cost of renting each month for num_months months.

		Returns:
			List[float]: monthly cost of renting in dollars rounded to two
				decimal points.

		Raises:
			AssertionError: If num_months is not positive
		"""
		assert num_months > 0
		monthly_costs = []
		total_monthly_cost = self._get_total_monthly_cost()
		for month in range(num_months):
			monthly_cost = round(total_monthly_cost * (1+self.annual_rent_inflation)**(month // 12), 2)
			monthly_costs.append(monthly_cost)
		return monthly_costs


if __name__ == "__main__":
	print("Parsing rent config")
	c = RentConfig.parse_rent_config()
	print(c)
	print(c.get_monthly_costs_of_renting(25))
	print("Done parsing rent config")
