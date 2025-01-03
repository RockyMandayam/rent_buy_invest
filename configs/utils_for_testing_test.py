import math

# isort: off
from rent_buy_invest.configs.utils_for_testing import (
    check_filepath_field,
    check_float_field,
)

# isort: on
from rent_buy_invest.utils import io_utils


def test_check_float_field() -> None:
    class FloatFieldTestClass:
        class FloatFieldNestedTestClass:
            def __init__(self, x: float) -> None:
                assert math.isfinite(x) and x > 0 and x <= 1

        def __init__(self, nested: dict):
            self.nested = FloatFieldTestClass.FloatFieldNestedTestClass(**nested)

    check_float_field(
        FloatFieldTestClass,
        {"nested": {"x": 0.5}},
        ["nested", "x"],
        False,
        False,
        False,
    )


def test_check_filepath_field() -> None:
    class FilepathFieldTestClass:
        class FilepathFieldNestedTestClass:
            def __init__(self, filepath: str) -> None:
                io_utils.read_yaml(filepath)

        def __init__(self, nested: dict):
            self.nested = FilepathFieldTestClass.FilepathFieldNestedTestClass(**nested)

    check_filepath_field(
        FilepathFieldTestClass,
        {"nested": {"filepath": ""}},
        ["nested", "filepath"],
    )
