from copy import deepcopy

import jsonschema
import pytest

from rent_buy_invest.configs.experiment_config import ExperimentConfig

# isort: off
from rent_buy_invest.configs.utils_for_testing import (
    check_filepath_field,
    check_float_field,
)

# isort: on
from rent_buy_invest.utils import io_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
TEST_CONFIG_KWARGS = io_utils.read_yaml(TEST_CONFIG_PATH)
EXPERIMENT_CONFIG = ExperimentConfig.parse(TEST_CONFIG_PATH)


class TestExperimentConfig:
    def test_inputs_with_invalid_schema(self) -> None:
        # for now, can't use EXPERIMENT_CONFIG.__dict__ has for example 'market_config' not 'market_config_path'
        attributes = [
            "num_months",
            "market_config_path",
            "rent_config_path",
            "buy_config_path",
            "start_date",
        ]
        dir = f"rent_buy_invest/temp/experiment_config_test/TestExperimentConfig"
        for attribute in attributes:
            # error_type = AssertionError if attribute == "start_date" else jsonschema.ValidationError
            test_config_kwargs_copy = deepcopy(TEST_CONFIG_KWARGS)
            # first try null field
            test_config_kwargs_copy[attribute] = None
            project_path = (
                f"{dir}/test_inputs_with_invalid_schema_null_{attribute}.yaml"
            )
            io_utils.write_yaml(project_path, test_config_kwargs_copy)
            # for a null start date, jsonschema won't raise a validation error (it cannot test a datetime object)
            # an assertion error will be raised instead
            with pytest.raises(
                AssertionError
                if attribute == "start_date"
                else jsonschema.ValidationError
            ):
                ExperimentConfig.parse(project_path)
            # now try missing field
            del test_config_kwargs_copy[attribute]
            project_path = (
                f"{dir}/test_inputs_with_invalid_schema_missing_{attribute}.yaml"
            )
            io_utils.write_yaml(project_path, test_config_kwargs_copy)
            with pytest.raises(jsonschema.ValidationError):
                ExperimentConfig.parse(project_path)

        io_utils.delete_dir(dir)

    def test_invalid_inputs(self) -> None:
        check_float_field(
            ExperimentConfig,
            TEST_CONFIG_KWARGS,
            ["num_months"],
            allow_negative=False,
            allow_zero=False,
            max_value=ExperimentConfig.MAX_NUM_MONTHS,
        )
        check_filepath_field(
            ExperimentConfig,
            TEST_CONFIG_KWARGS,
            ["market_config_path"],
        )
        check_filepath_field(
            ExperimentConfig,
            TEST_CONFIG_KWARGS,
            ["rent_config_path"],
        )
        check_filepath_field(
            ExperimentConfig,
            TEST_CONFIG_KWARGS,
            ["buy_config_path"],
        )
