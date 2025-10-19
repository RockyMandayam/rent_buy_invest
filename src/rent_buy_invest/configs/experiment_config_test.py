from copy import deepcopy

import jsonschema
import pytest

from rent_buy_invest.configs.config_test import TestConfig
from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.utils_for_testing import (
    check_filepath_field,
    check_float_field,
)
from rent_buy_invest.io import io_utils


class TestExperimentConfig(TestConfig):
    TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"

    def test_inputs_with_invalid_schema(self) -> None:
        attributes = [
            "num_years",
            "market_config_path",
            "rent_config_path",
            "buy_config_path",
            "start_date",
        ]
        self._test_inputs_with_invalid_schema(ExperimentConfig, attributes)

    def test_invalid_inputs(self) -> None:
        test_config_kwargs = io_utils.read_yaml(TestExperimentConfig.TEST_CONFIG_PATH)
        check_float_field(
            ExperimentConfig,
            test_config_kwargs,
            ["num_years"],
            allow_negative=False,
            allow_zero=False,
            max_value=ExperimentConfig.MAX_NUM_YEARS,
        )
        check_filepath_field(
            ExperimentConfig,
            test_config_kwargs,
            ["market_config_path"],
        )
        check_filepath_field(
            ExperimentConfig,
            test_config_kwargs,
            ["rent_config_path"],
        )
        check_filepath_field(
            ExperimentConfig,
            test_config_kwargs,
            ["buy_config_path"],
        )
