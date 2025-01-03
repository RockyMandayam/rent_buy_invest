import jsonschema
import pytest

from rent_buy_invest.configs.experiment_config import ExperimentConfig

# isort: off
from rent_buy_invest.core.utils_for_testing import (
    check_filepath_field,
    check_float_field,
)

# isort: on
from rent_buy_invest.utils import io_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
EXPERIMENT_CONFIG = ExperimentConfig.parse(TEST_CONFIG_PATH)


class TestExperimentConfig:
    def test_inputs_with_invalid_schema(self) -> None:
        # check null fields
        attributes = [
            "num_months",
            "market_config_path",
            "rent_config_path",
            "buy_config_path",
        ]
        for attribute in attributes:
            test_config_filename = f"rent_buy_invest/core/test_resources/test-experiment-config_null_{attribute}.yaml"
            with pytest.raises(jsonschema.ValidationError):
                ExperimentConfig.parse(test_config_filename)
        # test start_date separately since jsonschema does not check this field (it cannot test a datetime object)
        with pytest.raises(AssertionError):
            ExperimentConfig.parse(
                "rent_buy_invest/core/test_resources/test-experiment-config_null_start_date.yaml"
            )

        # check missing field
        with pytest.raises(jsonschema.ValidationError):
            ExperimentConfig.parse(
                "rent_buy_invest/core/test_resources/test-experiment-config_missing_start_date.yaml"
            )

    def test_invalid_inputs(self) -> None:
        config_kwargs = io_utils.read_yaml(TEST_CONFIG_PATH)

        check_float_field(
            ExperimentConfig,
            config_kwargs,
            ["num_months"],
            allow_negative=False,
            allow_zero=False,
            max_value=ExperimentConfig.MAX_NUM_MONTHS,
        )
        check_filepath_field(
            ExperimentConfig,
            config_kwargs,
            ["market_config_path"],
        )
        check_filepath_field(
            ExperimentConfig,
            config_kwargs,
            ["rent_config_path"],
        )
        check_filepath_field(
            ExperimentConfig,
            config_kwargs,
            ["buy_config_path"],
        )
