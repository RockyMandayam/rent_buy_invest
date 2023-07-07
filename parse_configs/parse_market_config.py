import yaml


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

	def get_tax(income: float) -> float:
		"""Calculates tax owed given income.

		Args:
			income: non-negative income

		Returns:
			tax: non-negative tax owed
		"""
		tax = 0
		lower_limit = 0
		for bracket in tax_brackets:
			if income < lower_limit:
				break
			tax_rate, upper_limit = bracket['tax_rate'], bracket['upper_limit']
			if income <= upper_limit:
				tax += tax_rate * (income - lower_limit)
				break
			tax += tax_rate * (upper_limit - lower_limit)
			lower_limit = upper_limit
		return tax


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

	@staticmethod
	def parse_market_config() -> 'MarketConfig':
		""" Load market config yaml file as an instance of this class """
		# TODO replace this absolute path string literal
		with open("/Users/rocky/Downloads/rent-buy-invest/configs/market-config.yaml") as f:
			config = yaml.load(f)
		return config

if __name__ == "__main__":
	print("Parsing market config")
	c = MarketConfig.parse_market_config()
	print(c)
	print(c.__dict__)
	print(c.tax_brackets.tax_brackets[0])
	print("Done parsing market config")
