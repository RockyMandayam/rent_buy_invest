from dataclasses import dataclass

from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

# The IRS recovery period for residential rental real property: its cost is deducted in
# equal parts over 27.5 years.
# "Residential" here is about what the TENANT uses the building for, not about whether the
# owner lives there and not about whether the owner is running a business. A house or
# apartment rented to someone as their home is residential rental property, even though
# renting it out is a business for the owner. Property rented for business use -- offices,
# retail, warehouses -- is "nonresidential" and recovers over 39 years instead. This tool
# only models renting a home to someone who lives in it, so 39-year property never arises.
RESIDENTIAL_DEPRECIATION_YEARS = 27.5

# 330 months, after which the property is fully depreciated and nothing more can be deducted
RESIDENTIAL_DEPRECIATION_MONTHS = round(
    RESIDENTIAL_DEPRECIATION_YEARS * MONTHS_PER_YEAR
)


@dataclass(frozen=True)
class DepreciationSchedule:
    """Per-month straight-line depreciation of a rental property's building.

    ``monthly_depreciation[m]`` is the dollar amount of depreciation deducted for
    month ``m``, where month 0 is the first month the property is held. It is the
    same amount every month until the building is fully depreciated, and zero from
    then on. It is a deduction taken that month, not a running total and not the
    building's remaining value.
    """

    monthly_depreciation: list[float]

    def accumulated_through(self, month: int) -> float:
        """Total depreciation taken from month 0 through ``month``, inclusive.

        This is what reduces the property's cost basis at sale. Asking for a month
        past the end of the schedule returns the total taken over the whole
        schedule, since nothing accrues after it ends.
        """
        assert month >= 0
        return round(sum(self.monthly_depreciation[: month + 1]), 2)


def compute_depreciation_schedule(
    depreciable_basis: float, num_months: int
) -> DepreciationSchedule:
    """Project straight-line depreciation from month 0 through month ``num_months``.

    Returns a list of length ``num_months + 1`` (both endpoints included), matching
    the length of every other monthly projection in this tool.

    Only the building depreciates -- land does not -- so ``depreciable_basis`` is
    the building's share of the cost basis, which the caller works out. The basis is
    spread evenly across ``RESIDENTIAL_DEPRECIATION_MONTHS``, and the last of those
    months absorbs any rounding remainder so the schedule totals exactly the basis:
    a property can never be depreciated by more or less than what it cost.

    The IRS mid-month convention (a property placed in service mid-month gets half
    that month) is not modeled, consistent with the monthly approximation used
    elsewhere in this tool.
    """
    assert num_months > 0
    assert depreciable_basis >= 0

    monthly_amount = round(depreciable_basis / RESIDENTIAL_DEPRECIATION_MONTHS, 2)
    final_month = RESIDENTIAL_DEPRECIATION_MONTHS - 1

    monthly_depreciation: list[float] = []
    for month in range(num_months + 1):
        if month < final_month:
            monthly_depreciation.append(monthly_amount)
        elif month == final_month:
            # absorb the rounding remainder so the total is exactly the basis
            monthly_depreciation.append(
                round(depreciable_basis - monthly_amount * final_month, 2)
            )
        else:
            # fully depreciated
            monthly_depreciation.append(0)

    return DepreciationSchedule(monthly_depreciation=monthly_depreciation)
