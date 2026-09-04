import pytest

from rent_buy_invest.main import _cap_gains_from_selling_investments
from rent_buy_invest.utils.data_utils import to_df


def _projection(balances: list[float], surpluses: list[float]):
    """A minimal stand-in for the projection, with just the columns that matter."""
    return to_df(
        {
            "Rent: Invested (Pre-Tax)": balances,
            "Rent: Surplus": surpluses,
        },
        multi_col=True,
    )


def test_gain_excludes_the_money_that_was_paid_in() -> None:
    """Deposits are cost basis, not profit.

    A world that pays into the market every month is not taxed on its own
    deposits -- only on what those deposits earned.
    """
    # opens at 1,000, pays in 100 a month, and the market carries it to 1,500
    projection = _projection([1000, 1150, 1310, 1500], [100, 100, 100, 0])

    # basis is 1,000 opening + 300 deposited, so only the remaining 200 is gain
    assert _cap_gains_from_selling_investments(projection, "Rent") == pytest.approx(200)


def test_gain_ignores_the_final_months_surplus() -> None:
    """The last row's cash flow never lands, so it is not basis either.

    Calculator appends one extra balance and pops it, so the surplus shown in the
    final row never moved an account.
    """
    with_final = _projection([1000, 1150, 1310, 1500], [100, 100, 100, 500])
    without_final = _projection([1000, 1150, 1310, 1500], [100, 100, 100, 0])

    both = _cap_gains_from_selling_investments(with_final, "Rent")
    assert both == _cap_gains_from_selling_investments(without_final, "Rent")
    # and it is a real figure, not two zeros agreeing
    assert both > 0


def test_gain_is_the_whole_growth_when_nothing_was_paid_in() -> None:
    projection = _projection([1000, 1100, 1200, 1300], [0, 0, 0, 0])

    assert _cap_gains_from_selling_investments(projection, "Rent") == pytest.approx(300)


def test_a_loss_is_reported_as_no_gain() -> None:
    """TODO: losses are floored rather than deducted; see the helper's docstring."""
    projection = _projection([1000, 900, 800, 700], [0, 0, 0, 0])

    assert _cap_gains_from_selling_investments(projection, "Rent") == 0


def test_deposits_alone_are_never_taxed() -> None:
    """The exact bug this guards: a flat market that only received deposits."""
    # every dollar of growth came from deposits, so there is no gain at all
    projection = _projection([0, 100, 200, 300], [100, 100, 100, 0])

    assert _cap_gains_from_selling_investments(projection, "Rent") == 0
