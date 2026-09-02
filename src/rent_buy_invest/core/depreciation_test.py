import pytest

from rent_buy_invest.core.depreciation import (
    RESIDENTIAL_DEPRECIATION_MONTHS,
    compute_depreciation_schedule,
)

# 330 months, so a basis of 330,000 depreciates at exactly 1,000 a month
EVEN_BASIS = 330_000.0


def test_rejects_bad_input() -> None:
    with pytest.raises(AssertionError):
        compute_depreciation_schedule(EVEN_BASIS, 0)
    with pytest.raises(AssertionError):
        compute_depreciation_schedule(-1, 24)


def test_recovery_period_is_27_and_a_half_years() -> None:
    assert RESIDENTIAL_DEPRECIATION_MONTHS == 330


def test_spreads_the_basis_evenly() -> None:
    num_months = 24
    schedule = compute_depreciation_schedule(EVEN_BASIS, num_months)

    assert len(schedule.monthly_depreciation) == num_months + 1
    assert all(a == 1000 for a in schedule.monthly_depreciation)


def test_stops_once_fully_depreciated() -> None:
    schedule = compute_depreciation_schedule(
        EVEN_BASIS, RESIDENTIAL_DEPRECIATION_MONTHS + 24
    )

    # the last depreciating month is the 330th, at index 329
    assert schedule.monthly_depreciation[RESIDENTIAL_DEPRECIATION_MONTHS - 1] == 1000
    assert schedule.monthly_depreciation[RESIDENTIAL_DEPRECIATION_MONTHS] == 0
    assert all(
        a == 0 for a in schedule.monthly_depreciation[RESIDENTIAL_DEPRECIATION_MONTHS:]
    )


def test_totals_exactly_the_basis_despite_rounding() -> None:
    # 100,000 / 330 = 303.0303..., so the even monthly amount cannot sum to the basis
    basis = 100_000.0
    schedule = compute_depreciation_schedule(
        basis, RESIDENTIAL_DEPRECIATION_MONTHS + 24
    )

    assert schedule.monthly_depreciation[0] == 303.03
    # the final depreciating month takes up the remainder
    assert schedule.monthly_depreciation[RESIDENTIAL_DEPRECIATION_MONTHS - 1] != 303.03
    assert round(sum(schedule.monthly_depreciation), 2) == basis


def test_accumulated_through_sums_inclusively() -> None:
    schedule = compute_depreciation_schedule(EVEN_BASIS, 24)

    assert schedule.accumulated_through(0) == 1000
    assert schedule.accumulated_through(11) == 12_000
    assert schedule.accumulated_through(24) == 25_000


def test_accumulated_through_caps_at_the_full_basis() -> None:
    schedule = compute_depreciation_schedule(
        EVEN_BASIS, RESIDENTIAL_DEPRECIATION_MONTHS + 24
    )

    assert (
        schedule.accumulated_through(RESIDENTIAL_DEPRECIATION_MONTHS - 1) == EVEN_BASIS
    )
    # nothing accrues after the property is fully depreciated
    assert (
        schedule.accumulated_through(RESIDENTIAL_DEPRECIATION_MONTHS + 24) == EVEN_BASIS
    )


def test_accumulated_through_rejects_a_negative_month() -> None:
    schedule = compute_depreciation_schedule(EVEN_BASIS, 24)

    with pytest.raises(AssertionError):
        schedule.accumulated_through(-1)


def test_zero_basis_depreciates_nothing() -> None:
    # land-only, or a caller that has not assigned any value to the building
    schedule = compute_depreciation_schedule(0, 24)

    assert all(a == 0 for a in schedule.monthly_depreciation)
    assert schedule.accumulated_through(24) == 0
