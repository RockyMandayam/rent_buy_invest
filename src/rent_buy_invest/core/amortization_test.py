import pytest

from rent_buy_invest.core.amortization import compute_loan_amortization_schedule


def test_compute_loan_amortization_schedule_rejects_bad_input() -> None:
    with pytest.raises(AssertionError):
        compute_loan_amortization_schedule(1000, 0.05, 100, 0)
    with pytest.raises(AssertionError):
        compute_loan_amortization_schedule(-1, 0.05, 100, 12)
    with pytest.raises(AssertionError):
        compute_loan_amortization_schedule(1000, -0.01, 100, 12)
    with pytest.raises(AssertionError):
        compute_loan_amortization_schedule(1000, 0.05, -1, 12)


def test_compute_loan_amortization_schedule_rejects_payment_below_interest() -> None:
    # 200000 at 6% accrues 1000 of interest in month 0, so a 900 payment would
    # grow the balance forever
    with pytest.raises(AssertionError):
        compute_loan_amortization_schedule(200_000, 0.06, 900, 12)


def test_compute_loan_amortization_schedule_lengths_and_recurrence() -> None:
    num_months = 24
    schedule = compute_loan_amortization_schedule(200_000, 0.06, 1500, num_months)

    assert len(schedule.starting_balances) == num_months + 1
    assert len(schedule.interest_payments) == num_months + 1
    assert len(schedule.principal_payments) == num_months + 1

    # month 0: full balance; interest = 200000 * 0.06 / 12 = 1000
    assert schedule.starting_balances[0] == 200_000
    assert schedule.interest_payments[0] == 1000
    assert schedule.principal_payments[0] == 500  # 1500 payment - 1000 interest

    # month 1: balance dropped by month 0's principal, so less of the same
    # payment goes to interest and more goes to principal
    assert schedule.starting_balances[1] == 199_500
    assert schedule.interest_payments[1] == 997.5
    assert schedule.principal_payments[1] == 502.5

    for m in range(num_months + 1):
        assert (
            round(schedule.interest_payments[m] + schedule.principal_payments[m], 2)
            == 1500
        )


def test_compute_loan_amortization_schedule_projects_past_loan_term() -> None:
    # a payment that pays the loan off in 12 months, projected over 18
    schedule = compute_loan_amortization_schedule(12_000, 0.0, 1000, 18)

    assert schedule.starting_balances[11] == 1000
    assert schedule.starting_balances[12] == 0
    # once paid off, the loan contributes nothing for the rest of the horizon
    assert schedule.starting_balances[12:] == [0] * 7
    assert schedule.interest_payments[12:] == [0] * 7
    assert schedule.principal_payments[12:] == [0] * 7


def test_compute_loan_amortization_schedule_stops_short_of_payoff() -> None:
    # a 12-month horizon on a loan that takes far longer to pay off
    schedule = compute_loan_amortization_schedule(200_000, 0.06, 1500, 12)

    assert schedule.starting_balances[-1] > 0
    assert all(p > 0 for p in schedule.principal_payments)


def test_compute_loan_amortization_schedule_zero_interest() -> None:
    schedule = compute_loan_amortization_schedule(12_000, 0.0, 1000, 24)

    assert all(i == 0 for i in schedule.interest_payments)
    assert schedule.principal_payments[:12] == [1000] * 12


def test_compute_loan_amortization_schedule_no_loan() -> None:
    # an all-cash purchase: nothing borrowed, so nothing to amortize
    schedule = compute_loan_amortization_schedule(0, 0.05, 0, 12)

    assert schedule.starting_balances == [0] * 13
    assert schedule.interest_payments == [0] * 13
    assert schedule.principal_payments == [0] * 13


def test_compute_loan_amortization_schedule_final_partial_payment() -> None:
    # the payoff month pays only the balance left, not a full 2000
    schedule = compute_loan_amortization_schedule(5000, 0.12, 2000, 12)

    payoff_month = next(m for m, b in enumerate(schedule.starting_balances) if b == 0)
    last_paid_month = payoff_month - 1
    assert (
        schedule.principal_payments[last_paid_month]
        == schedule.starting_balances[last_paid_month]
    )
    assert (
        schedule.interest_payments[last_paid_month]
        + schedule.principal_payments[last_paid_month]
        < 2000
    )

    # principal repaid over the life of the loan equals the original balance
    assert round(sum(schedule.principal_payments), 2) == 5000
