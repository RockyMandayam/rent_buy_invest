import copy
from typing import Any, Dict, List, Type

import pytest

# TODO test this file
# TODO document this file


def _check_field(
    clz: Type,
    config_kwargs: Dict[str, Any],
    field_keys: List,
    invalid_values: List,
    exception_to_raise: Exception,
):
    assert field_keys, "field_keys must be a non-empty list"
    config_kwargs = copy.deepcopy(config_kwargs)
    field = config_kwargs
    for i in range(len(field_keys) - 1):
        field = field[field_keys[i]]
    for val in invalid_values:
        field[field_keys[-1]] = val
        with pytest.raises(exception_to_raise):
            clz(**config_kwargs)


def check_float_field(
    clz: Type,
    config_kwargs: Dict[str, Any],
    field_keys: List,
    allow_negative: bool = True,
    allow_zero: bool = True,
    allow_greater_than_one: bool = True,
) -> None:
    # NOTE: this func can also be used for ints. schema at least checks that finite floats are not passed in to an int field
    invalid_values = [float("nan"), float("inf"), float("-inf")]
    if not allow_negative:
        invalid_values.append(-1)
    if not allow_zero:
        invalid_values.append(0)
    if not allow_greater_than_one:
        invalid_values.append(1.1)
    _check_field(clz, config_kwargs, field_keys, invalid_values, AssertionError)


def check_filepath_field(
    clz: Type,
    config_kwargs: Dict[str, Any],
    field_keys: List,
) -> None:
    _check_field(clz, config_kwargs, field_keys, ["nonexistent_filepath"], ValueError)
    _check_field(
        clz,
        config_kwargs,
        field_keys,
        ["rent_buy_invest/nonexistent_filepath"],
        FileNotFoundError,
    )
