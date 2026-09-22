import pytest

from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.market_account import compute_market_account_schedule
from rent_buy_invest.core.tax import TaxableAmounts, TaxModule
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

NUM_MONTHS = 2 * MONTHS_PER_YEAR
# no tax on the first 100,000 of the year's income, 20% on gains above it
BRACKETS = {
    "ordinary_income_tax_brackets": [
        {"upper_limit": 100_000.0, "tax_rate": 0.0},
        {"upper_limit": float("inf"), "tax_rate": 0.3},
    ],
    "long_term_capital_gains_tax_brackets": [
        {"upper_limit": 100_000.0, "tax_rate": 0.0},
        {"upper_limit": float("inf"), "tax_rate": 0.2},
    ],
}
# the dividends stack above the whole 0% band, so every dollar is taxed at 20%
ABOVE_THE_ZERO_BAND = TaxableAmounts(ordinary_income=200_000.0)
NO_OTHER_INCOME = TaxableAmounts()


def _market_config(rate_of_return: float, dividend_yield: float) -> MarketConfig:
    return MarketConfig(
        market_rate_of_return=rate_of_return,
        market_dividend_yield=dividend_yield,
        tax_brackets_inflation=0.0,
        annual_inflation_rate=0.0,
        tax_brackets=BRACKETS,
    )


def _schedule(
    rate_of_return: float = 0.0,
    dividend_yield: float = 0.0,
    opening_balance: float = 0.0,
    deposits: list[float] | None = None,
    dividend_tax_base: TaxableAmounts = ABOVE_THE_ZERO_BAND,
):
    market_config = _market_config(rate_of_return, dividend_yield)
    return compute_market_account_schedule(
        opening_balance=opening_balance,
        opening_cost_basis=opening_balance,
        monthly_deposits=(
            deposits if deposits is not None else [0.0] * (NUM_MONTHS + 1)
        ),
        taxable_income_before_dividends_by_year=[dividend_tax_base]
        * (NUM_MONTHS // MONTHS_PER_YEAR),
        market_config=market_config,
        tax_module=TaxModule(market_config),
    )


def test_compute_market_account_schedule_covers_every_month() -> None:
    schedule = _schedule(opening_balance=1_000.0)

    for values in (schedule.balances, schedule.cost_bases, schedule.dividend_taxes):
        assert len(values) == NUM_MONTHS + 1


def test_compute_market_account_schedule_adds_each_deposit_the_next_month() -> None:
    """A deposit is basis as well as balance: it is your money, not gain.

    It first shows up at the start of the month after it was made, which is why
    the last month's deposit never appears at all.
    """
    deposits = [100.0] * (NUM_MONTHS + 1)
    schedule = _schedule(opening_balance=1_000.0, deposits=deposits)

    assert schedule.balances[0] == 1_000
    assert schedule.balances[1] == 1_100
    # every deposit but the last one landed
    assert schedule.balances[-1] == pytest.approx(1_000 + 100 * NUM_MONTHS)
    assert schedule.cost_bases == schedule.balances


def test_compute_market_account_schedule_grows_at_the_rate_of_return() -> None:
    """Growth is gain, not basis: the basis stays where it opened."""
    schedule = _schedule(rate_of_return=0.10, opening_balance=1_000.0)

    assert schedule.balances[MONTHS_PER_YEAR] == pytest.approx(1_100, abs=0.01)
    assert schedule.balances[2 * MONTHS_PER_YEAR] == pytest.approx(1_210, abs=0.01)
    assert all(cost_basis == 1_000 for cost_basis in schedule.cost_bases)
    assert all(tax == 0 for tax in schedule.dividend_taxes)


def test_compute_market_account_schedule_taxes_dividends_once_a_year() -> None:
    schedule = _schedule(
        rate_of_return=0.10, dividend_yield=0.05, opening_balance=1_000.0
    )

    assert any(tax > 0 for tax in schedule.dividend_taxes)
    for month, tax in enumerate(schedule.dividend_taxes):
        if month % MONTHS_PER_YEAR != MONTHS_PER_YEAR - 1:
            assert tax == 0, f"month {month} taxed dividends mid-year"
        else:
            assert tax != 0, f"dividend tax expected"


def test_compute_market_account_schedule_pays_dividend_tax_from_the_account() -> None:
    """The first year: 1,000 grows 10%, to 1,100.

    A 5% dividend yield is 5% of the balance, 50 -- half of that 100 of growth.
    Those 50 are taxed at 20%, so 10 comes out of the account and the 40 left
    stays invested. The 40 is basis now -- it has been taxed -- while the other
    50 of growth is still gain, untaxed until the sale.
    """
    schedule = _schedule(
        rate_of_return=0.10, dividend_yield=0.05, opening_balance=1_000.0
    )
    year_end = MONTHS_PER_YEAR - 1

    assert schedule.dividend_taxes[year_end] == pytest.approx(10, abs=0.01)
    assert schedule.balances[year_end + 1] == pytest.approx(1_100 - 10, abs=0.01)
    assert schedule.cost_bases[year_end + 1] == pytest.approx(1_000 + 40, abs=0.01)


def test_compute_market_account_schedule_does_not_tax_dividends_twice() -> None:
    """Pay the whole return out as dividends and nothing is left to tax at sale.

    Every dollar of growth is taxed in the year it arrives, so the balance and the
    basis agree: there is no gain left. Leaving the basis alone would tax the same
    dollars again when the account is sold.
    """
    schedule = _schedule(
        rate_of_return=0.10, dividend_yield=0.10, opening_balance=1_000.0
    )

    assert sum(schedule.dividend_taxes) > 0
    assert schedule.balances[-1] == pytest.approx(schedule.cost_bases[-1], abs=0.01)


def test_compute_market_account_schedule_taxes_dividends_on_top_of_the_base() -> None:
    """Which rate the dividends pay depends on the income beneath them.

    With nothing else that year they fall in the 0% band; stacked above it, they
    pay 20%.
    """
    alone = _schedule(
        rate_of_return=0.10,
        dividend_yield=0.05,
        opening_balance=1_000.0,
        dividend_tax_base=NO_OTHER_INCOME,
    )
    on_top = _schedule(
        rate_of_return=0.10,
        dividend_yield=0.05,
        opening_balance=1_000.0,
        dividend_tax_base=ABOVE_THE_ZERO_BAND,
    )
    year_end = MONTHS_PER_YEAR - 1

    assert alone.dividend_taxes[year_end] == 0
    assert on_top.dividend_taxes[year_end] == pytest.approx(10, abs=0.01)


def test_compute_market_account_schedule_uses_each_years_own_tax_base() -> None:
    """Year one's dividends stack on year one's income, year two's on year two's.

    With nothing else in year one they fall in the 0% band; in year two they
    stack above it and pay 20%. Getting the years mixed up would tax both alike.
    """
    market_config = _market_config(0.10, 0.05)
    schedule = compute_market_account_schedule(
        opening_balance=1_000.0,
        opening_cost_basis=1_000.0,
        monthly_deposits=[0.0] * (NUM_MONTHS + 1),
        taxable_income_before_dividends_by_year=[NO_OTHER_INCOME, ABOVE_THE_ZERO_BAND],
        market_config=market_config,
        tax_module=TaxModule(market_config),
    )

    assert schedule.dividend_taxes[MONTHS_PER_YEAR - 1] == 0
    assert schedule.dividend_taxes[2 * MONTHS_PER_YEAR - 1] > 0


def test_compute_market_account_schedule_needs_one_tax_base_per_year() -> None:
    market_config = _market_config(0.10, 0.05)
    with pytest.raises(AssertionError):
        compute_market_account_schedule(
            opening_balance=1_000.0,
            opening_cost_basis=1_000.0,
            monthly_deposits=[0.0] * (NUM_MONTHS + 1),
            # two years end inside the projection, but only one base is given
            taxable_income_before_dividends_by_year=[ABOVE_THE_ZERO_BAND],
            market_config=market_config,
            tax_module=TaxModule(market_config),
        )
