import itertools

import jsonschema
import pytest

from rent_buy_invest.configs.config_test import TestConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.configs.utils_for_testing import check_float_field
from rent_buy_invest.utils import io_utils
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


class TestPersonalConfig(TestConfig):
    TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-personal-config.yaml"
    PERSONAL_CONFIG = PersonalConfig.parse(TEST_CONFIG_PATH)

    def test_inputs_with_invalid_schema(self) -> None:
        # check null fields
        attributes = [
            "ordinary_income",
            "ordinary_income_growth_rate",
            "years_till_retirement",
        ]
        self._test_inputs_with_invalid_schema(PersonalConfig, attributes)

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TestPersonalConfig.TEST_CONFIG_PATH)

        check_float_field(
            PersonalConfig,
            config_kwargs,
            ["ordinary_income"],
            allow_negative=False,
        )
        check_float_field(
            PersonalConfig,
            config_kwargs,
            ["ordinary_income_growth_rate"],
            min_value=-1,
        )
        check_float_field(
            PersonalConfig,
            config_kwargs,
            ["years_till_retirement"],
            allow_negative=False,
        )
