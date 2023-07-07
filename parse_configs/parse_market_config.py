import yaml


class TaxBrackets(yaml.YAMLObject):
	"""Stores tax bracket config.

	Due to using yaml_tag = "!TaxBrackets", the yaml library handles auto-
	converting from a yaml file to an instance of this class. Therefore,
	the __init__ method is not used.
	"""

	yaml_tag = "!TaxBrackets"

	# __init__ method not used due to yaml.YAMLObject

	def get_tax(income):
		"""Calculates tax owed given income.

		Income must be non-negative. Tax is always non-negative.
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
	"""

	yaml_tag = "!MarketConfig"

	# __init__ method not used due to yaml.YAMLObject

	@staticmethod
	def parse_market_config():
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