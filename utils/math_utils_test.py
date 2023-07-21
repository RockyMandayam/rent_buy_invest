import pytest

from . import math_utils

def test_get_equivalent_monthly_compound_rate() -> None:
    annual_compound_rate = 4095 # unrealistic example, just trying with a nice int
    actual = math_utils.get_equivalent_monthly_compound_rate(annual_compound_rate)
    expected = 1
    assert actual == pytest.approx(expected)
    annual_compound_rate = 0.07 # unrealistic example, just trying with a nice int
    actual = math_utils.get_equivalent_monthly_compound_rate(annual_compound_rate)
    expected = 0.00565414539
    assert actual == pytest.approx(expected)

def test_get_monthly_costs() -> None:
    # TODO test all parameters
    principal = 1000
    annual_inflation_rate = 0.03
    num_months = 25

    actual = math_utils.project_growth(
        principal, annual_inflation_rate, False, num_months
    )
    expected = (
        [principal] * 12
        + [round(principal * 1.03, 2)] * 12
        + [round(principal * 1.03**2, 2)]
    )
    assert actual == expected
