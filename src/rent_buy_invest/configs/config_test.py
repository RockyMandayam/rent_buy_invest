from collections.abc import Collection, Sequence
from copy import deepcopy

import jsonschema
import pytest

from rent_buy_invest.configs.config import Config
from rent_buy_invest.io import io_utils


class TestConfig:
    # override this in subclasses
    TEST_CONFIG_PATH = ""

    def test_init(self) -> None:
        # Config should not be instantiable
        with pytest.raises(TypeError):
            config = Config()

    def _test_inputs_with_invalid_schema(
        self, clz, attributes, nullable_attributes: Collection[str, ...] | None = None
    ) -> None:
        nullable_attributes = nullable_attributes or []
        TEST_CONFIG_KWARGS = io_utils.read_yaml(self.TEST_CONFIG_PATH)
        dir = f"rent_buy_invest/temp/{clz}"
        for attribute in attributes:
            test_config_kwargs_copy = deepcopy(TEST_CONFIG_KWARGS)
            attribute_parent = test_config_kwargs_copy
            if not isinstance(attribute, str):
                for nested_attribute in attribute[:-1]:
                    attribute_parent = attribute_parent[nested_attribute]
                attribute = attribute[-1]
            # first try null field
            if attribute not in nullable_attributes:
                attribute_parent[attribute] = None
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
                    clz.parse(project_path)
            # now try missing field
            del attribute_parent[attribute]
            project_path = (
                f"{dir}/test_inputs_with_invalid_schema_missing_{attribute}.yaml"
            )
            io_utils.write_yaml(project_path, test_config_kwargs_copy)
            with pytest.raises(jsonschema.ValidationError):
                clz.parse(project_path)

        io_utils.delete_dir(dir)
