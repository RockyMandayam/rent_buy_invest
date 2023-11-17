import datetime
from typing import Tuple


def get_equivalent_monthly_compound_rate(annual_compound_rate: float) -> float:
    return (1 + annual_compound_rate) ** (1 / 12) - 1


def project_growth(
    principal: float,
    annual_growth_rate: float,
    compound_monthly: bool,
    num_months: int,
    round_to_cent: bool = True,
) -> float:
    """Given a principal (starting amount) and an annual growth rate, return
    the value each month for num_months months.

    Returns:
        List[float]: monthly value in dollars

    Raises:
        AssertionError: If principal is negative or num_months is not positive
    """
    assert principal >= 0
    assert num_months > 0
    if compound_monthly:
        equivalent_monthly_rate = get_equivalent_monthly_compound_rate(
            annual_growth_rate
        )
    monthly_values = []
    for month in range(num_months):
        if compound_monthly:
            monthly_value = principal * (1 + equivalent_monthly_rate) ** month
        else:
            monthly_value = principal * (1 + annual_growth_rate) ** (month // 12)
        if round_to_cent:
            monthly_value = round(monthly_value, 2)
        monthly_values.append(monthly_value)
    return monthly_values


def month_to_year_month(month: int) -> Tuple[int]:
    """Convert 0-indexed month to (1-indexed year, 1-indexed month).
    E.g., 11 becomes (0,12) and 12 becomes (1, 1).
    """
    assert month >= 0, "Month must be non-negative."
    return month // 12 + 1, month % 12 + 1


def increment_month(date: datetime.date) -> datetime.date:
    # not using dateutils b/c don't want to depend on it just for this one function
    year, month = date.year, date.month
    month += 1
    if month == 13:
        month = 1
        year += 1
    # just an approximate hacky way of avoiding having to deal with months ending on different dates
    day = min(date.day, 28)
    return date.replace(year=year, month=month, day=day)
