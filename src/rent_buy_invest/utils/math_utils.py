import datetime
from collections.abc import Iterable

MONTHS_PER_YEAR: int = 12


def avg(seq: Iterable[float]) -> float:
    if not seq:
        return 0
    return sum(seq) / len(seq)


def get_equivalent_monthly_compound_rate(annual_compound_rate: float) -> float:
    return (1 + annual_compound_rate) ** (1 / MONTHS_PER_YEAR) - 1


def project_growth(
    principal: float,
    annual_growth_rate: float,
    compound_monthly: bool,
    num_months: int,
    round_to_cent: bool = True,
) -> list[float]:
    """Given a principal (starting amount) and an annual growth rate, return a
    list containing the projected fund amount at the beginning of each month for
    num_months+1 months (the extra month is there to present the final amount after
    num_months months).

    Returns:
        list[float]: monthly value in dollars

    Raises:
        AssertionError: If principal or num_months is negative
    """
    assert principal >= 0, "Principal must be non-negative."
    assert num_months >= 0, "Number of months must be non-negative."
    if compound_monthly:
        equivalent_monthly_rate = get_equivalent_monthly_compound_rate(
            annual_growth_rate
        )
    monthly_values = []
    for month in range(num_months + 1):
        if compound_monthly:
            monthly_value = principal * (1 + equivalent_monthly_rate) ** month
        else:
            monthly_value = principal * (1 + annual_growth_rate) ** (
                month // MONTHS_PER_YEAR
            )
        if round_to_cent:
            monthly_value = round(monthly_value, 2)
        monthly_values.append(monthly_value)
    return monthly_values


def increment_month(date: datetime.date) -> datetime.date:
    """Given a datetime date, return a datetime date with the month incremented;
    if a year boundary is crossed, the year is appropriately incremented

    NOTE: The date is set to the 28 of the month since Feb has 28 days and the callers of
    this function do not care about the day, only the month.
    """
    # not using dateutils b/c don't want to depend on it just for this one function
    year, month = date.year, date.month
    month += 1
    if month == 13:
        month = 1
        year += 1
    # just an approximate hacky way of avoiding having to deal with months ending on different dates
    day = min(date.day, 28)
    return date.replace(year=year, month=month, day=day)
