import pytest

from rent_buy_invest.utils import math_utils


def test_get_equivalent_monthly_compound_rate() -> None:
    annual_compound_rate = 4095  # unrealistic example, just trying with a nice int
    actual = math_utils.get_equivalent_monthly_compound_rate(annual_compound_rate)
    expected = 1
    assert actual == pytest.approx(expected)
    annual_compound_rate = 0.07  # unrealistic example, just trying with a nice int
    actual = math_utils.get_equivalent_monthly_compound_rate(annual_compound_rate)
    expected = 0.00565414539
    assert actual == pytest.approx(expected)


def test_get_monthly_costs() -> None:
    # test negative principal
    principal = -1
    annual_growth_rate = 1.07
    compound_monthly = True
    num_months = 1
    with pytest.raises(AssertionError):
        math_utils.project_growth(
            principal, annual_growth_rate, compound_monthly, num_months
        )

    # test negative num_months
    principal = 0
    num_months = 0
    with pytest.raises(AssertionError):
        math_utils.project_growth(
            principal, annual_growth_rate, compound_monthly, num_months
        )

    # test compounding annually
    principal = 1000
    annual_growth_rate = 0.03
    compound_monthly = False
    num_months = 25
    actual = math_utils.project_growth(
        principal, annual_growth_rate, compound_monthly, num_months
    )
    expected = (
        [principal] * 12
        + [round(principal * 1.03, 2)] * 12
        + [round(principal * 1.03**2, 2)]
    )
    assert actual == expected

    # test compounding monthly
    compound_monthly = True
    actual = math_utils.project_growth(
        principal, annual_growth_rate, compound_monthly, num_months
    )
    equivalent_monthly_rate = math_utils.get_equivalent_monthly_compound_rate(
        annual_growth_rate
    )
    expected = [
        round(principal * (1 + equivalent_monthly_rate) ** m, 2)
        for m in range(num_months)
    ]
    assert actual == expected

    # test without rounding
    actual = math_utils.project_growth(
        principal, annual_growth_rate, compound_monthly, num_months, round_to_cent=False
    )
    equivalent_monthly_rate = math_utils.get_equivalent_monthly_compound_rate(
        annual_growth_rate
    )
    expected = [
        principal * (1 + equivalent_monthly_rate) ** m for m in range(num_months)
    ]
    assert actual == pytest.approx(expected)
