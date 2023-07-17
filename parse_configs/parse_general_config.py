import yaml

from ..utils import math_utils

class GeneralConfig(yaml.YAMLObject):
	# TODO test this class
	"""Stores general config.

	Due to using yaml_tag = "!GeneralConfig", the yaml library handles auto-
	converting from a yaml file to an instance of this class. Therefore,
	the __init__ method is not used.

	Documentation of the instance variable types:
		# TODO add documentation
		# TODO maybe just point to the yaml file
	"""

	yaml_tag: str = "!GeneralConfig"

	# __init__ method not used due to yaml.YAMLObject

	def _validate(self) -> None:
		"""Sanity checks the configs.

		Raises:
			AssertionError: If any general configs are invalid
		"""
		# make 150 if parameter and maybe appropriately update the yaml comment
		assert self.num_months > 0 and self.num_months < 150

	# TODO test this and all parse methods
	@staticmethod
	def parse_general_config() -> 'GeneralConfig':
		"""Load general config yaml file as an instance of this class
		
		Raises:
			AssertionError: If any general configs are invalid
		"""
		# TODO replace this absolute path string literal
		with open("/Users/rocky/Downloads/rent_buy_invest/configs/general-config.yaml") as f:
			general_config = yaml.load(f)
		general_config._validate()
		return general_config


if __name__ == "__main__":
	print("Parsing general config")
	c = GeneralConfig.parse_general_config()
	print(c)
	print("Done parsing general config")
