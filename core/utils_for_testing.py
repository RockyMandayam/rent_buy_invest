import copy
from typing import Any, Dict, Iterable, List, Type

import pytest

# TODO test this file


def _check_field(
    clz: Type,
    config_kwargs: Dict[str, Any],
    field_keys: List,
    invalid_values: Iterable,
    exception_to_raise: Exception,
) -> None:
    """Checks that certain values for a given key in config_kwargs cause an exception_to_raise
    exception when instantiating clz from config_kwargs

    For each value in invalid_values, that value replaces the value associated with the
    key specified by field_keys (details given below) in config_kwargs - then, when clz
    is instantiated using this modified config_kwargs, it is asserted that exception_to_raise
    is thrown.

    The given key is specified by field_keys, which is an ordered list of keys leading to the
    final key. E.g., if we want to replace the value associated 'key2' in the following dict:
    {'key1': {'key2': 'value'}}, field_keys would be ['key1', 'key2'].
    Sometimes insteada of a Dict we deal with a List, in which case instead of a string as a
    key, a field_keys element can be an int representing the index in the list.


    Args:
        clz: Class to instantiate
        config_kwargs: Kwargs when instantiating clz
        field_keys: Ordered list of keys leading to the final key-value pair to test
        invalid_values: Each value in invalid_values should, when replacing the exist value
            in config_kwargs for the given key, should cause exception_to_raise
        exception_to_raise: the exception that should be thrown for each invalid value
    """
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
    """Checks that for a given key in config_kwargs with a float value, invalid values
    (defined by the params) cause an exception when instantiating clz from config_kwargs.

    See _check_field for details/examples of how field_keys works

    Args:
        clz: Class to instantiate
        config_kwargs: Kwargs when instantiating clz
        field_keys: Ordered list of keys leading to the final key-value pair to test
        allow_negative: if True, negative numbers are considered invalid
        allow_zero: if True, zero is considered invalid
        allow_greater_than_one: if True, numbers greater than one are considered invalid
    """
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
    """Checks that for a given key in config_kwargs with a filepath value, invalid values
    cause an exception when instantiating clz from config_kwargs.

    See _check_field for details/examples of how field_keys works

    Args:
        clz: Class to instantiate
        config_kwargs: Kwargs when instantiating clz
        field_keys: Ordered list of keys leading to the final key-value pair to test
    """
    _check_field(clz, config_kwargs, field_keys, ["nonexistent_filepath"], ValueError)
    _check_field(
        clz,
        config_kwargs,
        field_keys,
        ["rent_buy_invest/nonexistent_filepath"],
        FileNotFoundError,
    )
