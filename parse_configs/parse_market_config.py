import yaml


class MarketConfig(yaml.YAMLObject):
	"""Stores tax bracket config.

	Due to using yaml_tag = "!MarketConfig", the yaml library handles auto-
	converting from a yaml file to an instance of this class. Therefore,
	the __init__ method is not used.

	Documentation of the instance variable types:
		self.tax_brackets ('TaxBrackets'): A TaxBrackets object.
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
			print(f"ALL BRACKETS: {self.tax_brackets}")
			print(income)
			tax = 0
			lower_limit = 0
			for bracket in self.tax_brackets:
				print("####")
				print(f"bracket: {bracket}")
				print(f"tax: {tax}")
				if income < lower_limit:
					print("1")
					break
				tax_rate, upper_limit = bracket['tax_rate'], bracket['upper_limit']
				if income <= upper_limit:
					print("2")
					print(tax_rate)
					print(income)
					print(lower_limit)
					tax += tax_rate * (income - lower_limit)
					break
				print("3")
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


if __name__ == "__main__":
	print("Parsing market config")
	c = MarketConfig.parse_market_config()
	print(c)
	print(c.__dict__)
	print(c.tax_brackets.tax_brackets[0])
	print("Done parsing market config")
