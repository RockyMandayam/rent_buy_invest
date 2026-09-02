from rent_buy_invest.core.amortization import compute_loan_amortization_schedule
from rent_buy_invest.core.mortgage_insurance import (
    FHA_MI_TERM_IF_BELOW_THRESHOLD,
    compute_mortgage_insurance_schedule,
)

PURCHASE_PRICE = 500_000
APPRAISAL_COST = 600
ANNUAL_MI_FRACTION = 0.012


def _schedule(
    initial_loan_amount: float,
    num_months: int,
    monthly_payment: float,
    annual_interest_rate: float = 0.06,
):
    return compute_loan_amortization_schedule(
        initial_loan_amount, annual_interest_rate, monthly_payment, num_months
    )


def _compute(amortization_schedule, is_fha_loan: bool, initial_loan_amount: float):
    return compute_mortgage_insurance_schedule(
        amortization_schedule,
        is_fha_loan,
        initial_loan_amount,
        initial_loan_amount / PURCHASE_PRICE,
        PURCHASE_PRICE,
        ANNUAL_MI_FRACTION,
        APPRAISAL_COST,
    )


def test_lengths_match_the_amortization_schedule() -> None:
    schedule = _schedule(450_000, 24, 3000)
    mi = _compute(schedule, False, 450_000)

    assert len(mi.premiums) == len(schedule.starting_balances)
    assert len(mi.appraisal_costs) == len(schedule.starting_balances)


def test_conventional_owes_pmi_while_above_the_ltv_threshold() -> None:
    # 450k on a 500k home is 90% LTV, so PMI is owed from the start
    schedule = _schedule(450_000, 24, 3000)
    mi = _compute(schedule, False, 450_000)

    expected_premium = round(ANNUAL_MI_FRACTION * 450_000 / 12, 2)
    assert mi.premiums[0] == expected_premium
    assert all(p == expected_premium for p in mi.premiums)
    # the balance never reaches 80% of 500k within 24 months, so no appraisal
    assert all(c == 0 for c in mi.appraisal_costs)


def test_conventional_owes_no_pmi_when_starting_below_the_ltv_threshold() -> None:
    # 400k on a 500k home is exactly 80% LTV, so PMI is never owed
    schedule = _schedule(400_000, 24, 3000)
    mi = _compute(schedule, False, 400_000)

    assert all(p == 0 for p in mi.premiums)
    # no PMI was ever being paid, so there is nothing to drop and no appraisal
    assert all(c == 0 for c in mi.appraisal_costs)


def test_conventional_pays_for_one_appraisal_when_pmi_drops() -> None:
    # a large payment drives the balance below 80% of 500k partway through
    schedule = _schedule(410_000, 24, 8000)
    mi = _compute(schedule, False, 410_000)

    drop_month = next(m for m, p in enumerate(mi.premiums) if p == 0)
    assert drop_month > 0, "PMI should be owed at first, then drop"
    assert mi.appraisal_costs[drop_month] == APPRAISAL_COST
    # the appraisal is a one-off: it is paid in exactly one month
    assert sum(1 for c in mi.appraisal_costs if c != 0) == 1
    # and PMI never comes back
    assert all(p == 0 for p in mi.premiums[drop_month:])


def test_fha_above_threshold_owes_mi_for_the_life_of_the_loan() -> None:
    # 465k on a 500k home is 93% LTPP, above the 90% lifelong-MI threshold
    num_months = FHA_MI_TERM_IF_BELOW_THRESHOLD + 24
    schedule = _schedule(465_000, num_months, 3000)
    mi = _compute(schedule, True, 465_000)

    expected_premium = round(ANNUAL_MI_FRACTION * 465_000 / 12, 2)
    assert all(p == expected_premium for p in mi.premiums)
    # the 11-year cutoff must not apply to this loan
    assert mi.premiums[FHA_MI_TERM_IF_BELOW_THRESHOLD] == expected_premium


def test_fha_below_threshold_owes_mi_for_only_the_fixed_term() -> None:
    # 440k on a 500k home is 88% LTPP, at or below the 90% threshold
    num_months = FHA_MI_TERM_IF_BELOW_THRESHOLD + 24
    schedule = _schedule(440_000, num_months, 3000)
    mi = _compute(schedule, True, 440_000)

    expected_premium = round(ANNUAL_MI_FRACTION * 440_000 / 12, 2)
    assert all(
        p == expected_premium for p in mi.premiums[:FHA_MI_TERM_IF_BELOW_THRESHOLD]
    )
    assert all(p == 0 for p in mi.premiums[FHA_MI_TERM_IF_BELOW_THRESHOLD:])
    # FHA MI has no LTV-based drop, so the borrower never buys an appraisal
    assert all(c == 0 for c in mi.appraisal_costs)


def test_nothing_is_owed_once_the_loan_is_paid_off() -> None:
    # pays off well before the projection ends
    schedule = _schedule(450_000, 24, 60_000)
    mi = _compute(schedule, False, 450_000)

    payoff_month = next(m for m, b in enumerate(schedule.starting_balances) if b == 0)
    assert all(p == 0 for p in mi.premiums[payoff_month:])
