from dataclasses import dataclass

from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


@dataclass(frozen=True)
class LoanAmortizationSchedule:
    """Per-month balance and payment split for a fixed-payment loan.

    The three lists are of equal length and indexed by month, where month 0 is the
    loan's first month. For month ``m``, ``starting_balance[m]`` is the balance
    owed before that month's payment, and ``interest[m]`` and ``principal[m]``
    are how that month's payment divides between the two.

    A schedule covers however many months the caller asked to project, which is
    not necessarily long enough to pay the loan off -- a 30-year loan projected
    over a 10-year horizon ends with most of its balance still owed.
    """

    starting_balances: list[float]
    interest_payments: list[float]
    principal_payments: list[float]


def compute_loan_amortization_schedule(
    initial_loan_amount: float,
    annual_interest_rate: float,
    monthly_payment: float,
    num_months: int,
) -> LoanAmortizationSchedule:
    """Project a fixed-payment loan from month 0 through month ``num_months``.

    Returns lists of length ``num_months + 1`` (both endpoints included), which
    is the length every other monthly projection in this tool uses.

    Interest for a month is the balance at the start of that month times
    ``annual_interest_rate / MONTHS_PER_YEAR``. That simple division is
    deliberate: it is how mortgages actually charge interest, as opposed to an
    equivalent monthly compound rate. Whatever is left of ``monthly_payment``
    pays down principal, except in the payoff month, when only the remaining
    balance is paid. Amounts are rounded to the cent each month, as elsewhere in
    the projection.

    Sizing ``monthly_payment`` is the caller's job (for a mortgage, see
    ``BuyConfig.get_monthly_mortgage_payment``); it determines whether the loan
    is paid off within ``num_months``.
    """
    assert num_months > 0
    assert initial_loan_amount >= 0
    assert annual_interest_rate >= 0
    assert monthly_payment >= 0

    starting_balance: list[float] = []
    interest: list[float] = []
    principal: list[float] = []

    balance = initial_loan_amount
    for _ in range(num_months + 1):
        starting_balance.append(balance)

        month_interest = round(balance * annual_interest_rate / MONTHS_PER_YEAR, 2)
        if balance == 0:
            # nothing owed: either already paid off, or never borrowed at all
            month_principal = 0
        elif balance + month_interest <= monthly_payment:
            # payoff month: the interest plus the whole remaining balance fit
            # inside one regular payment
            month_principal = balance
        else:
            month_principal = round(monthly_payment - month_interest, 2)
            # TODO add an intial check that monthly payment is not less than interest...
            assert month_principal > 0, (
                "monthly_payment does not cover the month's interest, so the "
                "balance would grow instead of amortizing"
            )

        interest.append(month_interest)
        principal.append(month_principal)
        balance -= month_principal

    return LoanAmortizationSchedule(
        starting_balances=starting_balance,
        interest_payments=interest,
        principal_payments=principal,
    )
