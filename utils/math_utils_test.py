import datetime

import pytest

from rent_buy_invest.utils import math_utils


def test_avg() -> None:
    assert math_utils.avg([]) == 0
    assert math_utils.avg([0]) == 0
    assert math_utils.avg([0, 0]) == 0
    assert math_utils.avg([1, -1]) == 0
    assert math_utils.avg(range(1, 4)) == 2
    assert math_utils.avg(range(4)) == 1.5
    assert math_utils.avg([3, 0, 1, 0]) == 1


def test_get_equivalent_monthly_compound_rate() -> None:
    annual_compound_rate = 4095  # unrealistic example, just trying with a nice int
    actual = math_utils.get_equivalent_monthly_compound_rate(annual_compound_rate)
    expected = 1
    assert actual == pytest.approx(expected)
    annual_compound_rate = 0.07  # unrealistic example, just trying with a nice int
    actual = math_utils.get_equivalent_monthly_compound_rate(annual_compound_rate)
    expected = 0.00565414539
    assert actual == pytest.approx(expected)


def test_project_growth() -> None:
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
        [principal] * math_utils.MONTHS_PER_YEAR
        + [round(principal * 1.03, 2)] * math_utils.MONTHS_PER_YEAR
        + [round(principal * 1.03**2, 2)] * 2
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
        for m in range(num_months + 1)
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
        principal * (1 + equivalent_monthly_rate) ** m for m in range(num_months + 1)
    ]
    assert actual == pytest.approx(expected)


def test_month_to_year_month() -> None:
    with pytest.raises(AssertionError):
        math_utils.month_to_year_month(-1)
    assert math_utils.month_to_year_month(0) == (1, 1)
    assert math_utils.month_to_year_month(13) == (2, 2)


def test_increment_month() -> None:
    date = datetime.datetime.strptime("2020-09-03", "%Y-%m-%d")
    act = math_utils.increment_month(date)
    exp = date.replace(month=10)
    assert act == exp

    date = datetime.datetime.strptime("2020-01-31", "%Y-%m-%d")
    act = math_utils.increment_month(date)
    exp = date.replace(month=2, day=28)
    assert act == exp

    date = datetime.datetime.strptime("2020-12-31", "%Y-%m-%d")
    act = math_utils.increment_month(date)
    exp = date.replace(year=2021, month=1, day=28)
    assert act == exp
