import pytest

from rent_buy_invest.core.points_amortization import (
    compute_points_amortization_schedule,
)

FEE = 8_000.0
TERM = 360


def test_rejects_bad_input() -> None:
    with pytest.raises(AssertionError):
        compute_points_amortization_schedule(FEE, TERM, 0)
    with pytest.raises(AssertionError):
        compute_points_amortization_schedule(FEE, 0, 24)
    with pytest.raises(AssertionError):
        compute_points_amortization_schedule(-1, TERM, 24)


def test_covers_month_zero_through_num_months() -> None:
    schedule = compute_points_amortization_schedule(FEE, TERM, 24)
    assert len(schedule.monthly_deduction) == 25


def test_spreads_the_fee_evenly_across_the_loan_term() -> None:
    schedule = compute_points_amortization_schedule(FEE, TERM, 24)

    expected = round(FEE / TERM, 2)
    assert schedule.monthly_deduction[0] == expected
    assert all(d == expected for d in schedule.monthly_deduction)


def test_stops_deducting_once_the_loan_term_ends() -> None:
    schedule = compute_points_amortization_schedule(FEE, TERM, TERM + 12)

    assert schedule.monthly_deduction[TERM - 1] > 0
    assert schedule.monthly_deduction[TERM] == 0
    assert all(d == 0 for d in schedule.monthly_deduction[TERM:])


def test_totals_exactly_the_fee_paid_despite_rounding() -> None:
    # 8000 / 360 = 22.222..., so an even monthly amount cannot sum to the fee
    schedule = compute_points_amortization_schedule(FEE, TERM, TERM + 12)

    assert schedule.monthly_deduction[0] == 22.22
    # the final month of the term takes up the remainder
    assert schedule.monthly_deduction[TERM - 1] != 22.22
    assert round(sum(schedule.monthly_deduction), 2) == FEE


def test_accumulated_and_unamortized_always_total_the_fee() -> None:
    """Whatever the horizon, every dollar paid is either deducted or still owed."""
    for num_months in (1, 24, TERM - 1, TERM, TERM + 12):
        schedule = compute_points_amortization_schedule(FEE, TERM, num_months)
        for month in (0, 1, num_months):
            taken = schedule.accumulated_through(month)
            left = schedule.unamortized_remainder_after(month)
            assert round(taken + left, 2) == FEE, (num_months, month)


def test_unamortized_remainder_looks_past_the_end_of_the_projection() -> None:
    """A 30-year loan projected over 2 years still has most of the fee undeducted.

    The remainder is measured against the fee paid, not against the rest of the
    schedule, which only runs as far as the projection does.
    """
    schedule = compute_points_amortization_schedule(FEE, TERM, 24)

    assert schedule.accumulated_through(24) == pytest.approx(25 * 22.22)
    assert schedule.unamortized_remainder_after(24) == pytest.approx(FEE - 25 * 22.22)
    # far more is left than the projection itself lists
    assert schedule.unamortized_remainder_after(24) > sum(schedule.monthly_deduction)


def test_nothing_is_left_once_the_term_is_over() -> None:
    schedule = compute_points_amortization_schedule(FEE, TERM, TERM + 12)

    assert schedule.accumulated_through(TERM - 1) == pytest.approx(FEE)
    assert schedule.unamortized_remainder_after(TERM - 1) == 0
    assert schedule.unamortized_remainder_after(TERM + 12) == 0


def test_no_points_paid_deducts_nothing() -> None:
    schedule = compute_points_amortization_schedule(0, TERM, 24)

    assert all(d == 0 for d in schedule.monthly_deduction)
    assert schedule.accumulated_through(24) == 0
    assert schedule.unamortized_remainder_after(24) == 0


def test_rejects_a_negative_month() -> None:
    schedule = compute_points_amortization_schedule(FEE, TERM, 24)
    with pytest.raises(AssertionError):
        schedule.accumulated_through(-1)
    with pytest.raises(AssertionError):
        schedule.unamortized_remainder_after(-1)
