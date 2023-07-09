import yaml


class MarketConfig(yaml.YAMLObject):
	"""Stores market config.

	Due to using yaml_tag = "!MarketConfig", the yaml library handles auto-
	converting from a yaml file to an instance of this class. Therefore,
	the __init__ method is not used.

	Documentation of the instance variable types:
		self.market_rate_of_return (float): ANNUAL rate of return in the market, as a decimal
		self.tax_brackets ('TaxBrackets'): A TaxBrackets object
	"""

	yaml_tag: str = "!MarketConfig"

	# __init__ method not used due to yaml.YAMLObject

	class TaxBrackets(yaml.YAMLObject):
		"""Stores tax bracket config.

		Due to using yaml_tag = "!TaxBrackets", the yaml library handles auto-
		converting from a yaml file to an instance of this class. Therefore,
		the __init__ method is not used.

		Documentation of the instance variable types:
			self.tax_brackets (List[Dict[str, float]]): A list of tax brackets,
				where each bracket contains two keys, "upper_limit" and "tax_rate".
				"tax_rate" is the marginal tax rate of that bracket. "upper_limit"
				is the upper income limit of that bracket (beyond that limit, the
				next tax bracket begins). This list is ordered from lowest tax
				bracket to highest tax bracket. The highest tax bracket will have
				an upper limit of positive infinity.
		"""

		yaml_tag: str = "!TaxBrackets"

		# __init__ method not used due to yaml.YAMLObject

		def _validate(self) -> None:
			"""Sanity checks the configs.

			Raises:
				AssertionError: If any tax brackets configs are invaalid
			"""
			assert self.tax_brackets
			upper_limit = 0
			tax_rate = -1
			for bracket in self.tax_brackets:
				assert bracket["upper_limit"] > upper_limit
				assert bracket["tax_rate"] > tax_rate
				upper_limit = bracket["upper_limit"]
				tax_rate = bracket["tax_rate"]
			assert self.tax_brackets[-1]["upper_limit"] == float('inf')


		def get_tax(self, income: float) -> float:
			"""Calculates tax owed given income.

			Args:
				income: non-negative income

			Returns:
				tax: non-negative tax owed
			"""
			tax = 0
			lower_limit = 0
			for bracket in self.tax_brackets:
				if income < lower_limit:
					break
				tax_rate, upper_limit = bracket['tax_rate'], bracket['upper_limit']
				if income <= upper_limit:
					tax += tax_rate * (income - lower_limit)
					break
				tax += tax_rate * (upper_limit - lower_limit)
				lower_limit = upper_limit
			return tax

	def _validate(self) -> None:
		"""Sanity checks the configs.

		Raises:
			AssertionError: If any market configs are invalid
		"""
		assert self.tax_brackets is not None
		self.tax_brackets._validate()

	@staticmethod
	def parse_market_config() -> 'MarketConfig':
		"""Load market config yaml file as an instance of this class
		
		Raises:
			AssertionError: If any market configs are invalid
		"""
		# TODO replace this absolute path string literal
		with open("/Users/rocky/Downloads/rent_buy_invest/configs/market-config.yaml") as f:
			market_config = yaml.load(f)
		market_config._validate()
		return market_config

	def get_tax(self, income: float) -> float:
		"""Calculates tax owed given income.

		Args:
			income: non-negative income

		Returns:
			tax: non-negative tax owed
		"""
		return self.tax_brackets.get_tax(income)

	def get_pretax_monthly_wealth(self, principal: float, num_months: int) -> float:
		"""Return the pretax wealth in the market at the BEGINNING of each month
		for num_months months.

		Wealth refers to the total amount of money in the market, not the
		return (which refers to just the difference in wealth between one month
		and the previous month).

		NOTE: The annual rate of return is given by the configs. To make some
		calculations easier, an "equivalent" monthly rate of return is
		calculated such that compounding the monthly rate every month results
		in an annual growth of the given annual rate of return. Thus,
		compounding the monthly rate every month for 24 months is also
		equivalent to compounding the annual rate every year for 2 years.

		Math equations:
			Let a = annual rate of return, compounded annually
			Let m = "equivalent" monthly rate of return, compounded monthly
			We are given a and want to find m
			After one year, principal grows to:
				If compounding annually: (1 + a) * principal
				If compounding monthly: (1 + m)**12 * principal
			They should be equal:
				(1 + a) * principal = (1 + m)**12 * principal
				(1 + a) = (1 + m)**12
				(1 + a)**(1/12) = 1 + m
				m = (1 + a)**(1/12) - 1
			E.g., if the annual rate of return compounded annually is 0.12
			(12%), the monthly rate of return compounded monthly is
			0.00948879293.
		
		Returns:
			List[float]: monthly wealth in dollars at th beginning of each month
				rounded to two decimal points.

		Raises:
			AssertionError: If the principal is negative or num_months is not positive
		"""
		assert principal >= 0
		assert num_months > 0

		equivalent_monthly_return = (1 + self.market_rate_of_return)**(1/12) - 1
		monthly_wealths = []
		for month in range(num_months):
			wealth = round((1 + equivalent_monthly_return)**month * principal, 2)
			monthly_wealths.append(wealth)
		return monthly_wealths


if __name__ == "__main__":
	print("Parsing market config")
	c = MarketConfig.parse_market_config()
	print(c)
	print(c.__dict__)
	print(c.tax_brackets.tax_brackets[0])
	print("Done parsing market config")
