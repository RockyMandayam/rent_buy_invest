from dataclasses import dataclass


@dataclass(frozen=True)
class PointsAmortizationSchedule:
    """Per-month deduction for mortgage discount points on a rental property.

    Points are a fee paid at closing to buy down the interest rate. The money
    leaves your account once, on day one -- but for a rental you cannot deduct it
    all at once. It is spread evenly across the life of the loan, so this schedule
    changes only what you are taxed on, never what is in your bank account. That
    cash outlay is already counted among the upfront costs.

    ``monthly_deduction[m]`` is the dollar amount deducted for month ``m``, where
    month 0 is the loan's first month. It is the same amount every month until the
    loan term ends, and zero from then on. It is a deduction taken that month, not
    a running total and not the amount of points left to deduct.

    A home you live in is treated the opposite way: its points are deducted in full
    the year you pay them. That is what ``InitialState`` does for the rent-vs-buy
    comparison, and it does not apply here.
    """

    monthly_deduction: list[float]
    # what was paid at closing, kept because the projection usually ends long
    # before the loan term does, leaving part of it still undeducted
    discount_points_fee: float

    def accumulated_through(self, month: int) -> float:
        """Total deducted from month 0 through ``month``, inclusive."""
        assert month >= 0
        return round(sum(self.monthly_deduction[: month + 1]), 2)

    def unamortized_remainder_after(self, month: int) -> float:
        """Points paid for but not yet deducted as of the end of ``month``.

        Selling the property ends the loan early, and whatever is left undeducted
        can be taken in full in the year of the sale. Nothing is stranded: you
        eventually deduct every dollar you paid, either monthly or all at once when
        you sell.

        Measured against the fee paid rather than the rest of the schedule, because
        a 30-year loan projected over 10 years has 20 years of deductions that the
        schedule never lists.
        """
        assert month >= 0
        return round(self.discount_points_fee - self.accumulated_through(month), 2)


def compute_points_amortization_schedule(
    discount_points_fee: float,
    mortgage_term_months: int,
    num_months: int,
) -> PointsAmortizationSchedule:
    """Spread ``discount_points_fee`` evenly across the loan's term.

    Returns a list of length ``num_months + 1`` (both endpoints included), matching
    every other monthly projection in this tool.

    The fee is divided across ``mortgage_term_months``, and the last of those
    months absorbs any rounding remainder so the schedule totals exactly the fee --
    you deduct what you paid, no more and no less. If the projection runs past the
    end of the loan term, the later months deduct nothing; if it stops short, the
    undeducted balance is what ``unamortized_remainder_after`` reports.
    """
    assert num_months > 0
    assert mortgage_term_months > 0
    assert discount_points_fee >= 0

    monthly_amount = round(discount_points_fee / mortgage_term_months, 2)
    final_month = mortgage_term_months - 1

    monthly_deduction: list[float] = []
    for month in range(num_months + 1):
        if month < final_month:
            monthly_deduction.append(monthly_amount)
        elif month == final_month:
            # absorb the rounding remainder so the total is exactly the fee paid
            monthly_deduction.append(
                round(discount_points_fee - monthly_amount * final_month, 2)
            )
        else:
            # loan term is over; there is nothing left to deduct
            monthly_deduction.append(0)

    return PointsAmortizationSchedule(
        monthly_deduction=monthly_deduction,
        discount_points_fee=discount_points_fee,
    )
