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
            "mode",
            "num_years",
            "market_config_path",
            "rent_config_path",
            "buy_config_path",
            "start_date",
        ]
        # rent_config_path is nullable: RENTAL_VS_INVEST has no rent side
        nullable_attributes = ("rent_config_path",)
        self._test_inputs_with_invalid_schema(
            ExperimentConfig, attributes, nullable_attributes
        )

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

    def test_mode_must_be_one_of_the_known_comparisons(self) -> None:
        config_kwargs = deepcopy(
            io_utils.read_yaml(TestExperimentConfig.TEST_CONFIG_PATH)
        )
        config_kwargs["mode"] = "something_else"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                instance=config_kwargs,
                schema=io_utils.read_json(ExperimentConfig.schema_path()),
            )

    def test_rent_vs_buy_requires_a_rent_config(self) -> None:
        """That comparison has a rent side, so it needs one."""
        config_kwargs = deepcopy(
            io_utils.read_yaml(TestExperimentConfig.TEST_CONFIG_PATH)
        )
        config_kwargs["mode"] = ExperimentConfig.RENT_VS_BUY
        config_kwargs["rent_config_path"] = None
        with pytest.raises(AssertionError):
            ExperimentConfig(**config_kwargs)

    def test_rental_vs_invest_refuses_a_rent_config(self) -> None:
        """That comparison has no rent side, so a rent config would do nothing.

        Rejecting it is the point: a config file that changes no number is worse
        than an absent one, because a reader assumes it matters.
        """
        config_kwargs = deepcopy(
            io_utils.read_yaml(TestExperimentConfig.TEST_CONFIG_PATH)
        )
        config_kwargs["mode"] = ExperimentConfig.RENTAL_VS_INVEST
        with pytest.raises(AssertionError):
            ExperimentConfig(**config_kwargs)

        # and with it removed, the same config parses
        config_kwargs["rent_config_path"] = None
        experiment_config = ExperimentConfig(**config_kwargs)
        assert experiment_config.rent_config is None

    def test_rental_vs_invest_needs_a_buy_config_that_is_a_rental(self) -> None:
        """A home you live in earns no rent and is not depreciated.

        Without this the mismatch surfaces later, inside RentalProperty, rather
        than when the config that caused it is read.
        """
        config_kwargs = deepcopy(
            io_utils.read_yaml(TestExperimentConfig.TEST_CONFIG_PATH)
        )
        config_kwargs["mode"] = ExperimentConfig.RENTAL_VS_INVEST
        config_kwargs["rent_config_path"] = None
        config_kwargs[
            "buy_config_path"
        ] = "rent_buy_invest/core/test_resources/test-primary-residence-buy-config.yaml"
        with pytest.raises(AssertionError):
            ExperimentConfig(**config_kwargs)
