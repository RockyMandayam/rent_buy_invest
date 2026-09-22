from dataclasses import dataclass

from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.tax import TaxableAmounts, TaxModule
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


@dataclass(frozen=True)
class MarketAccountSchedule:
    """One market account, month by month, in dollars.

    The three lists are of equal length and indexed by month, month 0 through the
    last month of the projection inclusive.

    ``balances[m]`` is what the account holds at the START of month ``m``: a
    balance, not a flow. ``balances[0]`` is the opening balance.

    ``cost_bases[m]`` is the account's cost basis at the same moment: the part of
    ``balances[m]`` that is not gain, and so would not be taxed if the account
    were sold then. It is every dollar paid in, plus every dividend that was taxed
    in its own year and stayed invested.

    ``dividend_taxes[m]`` is the tax paid on dividends DURING month ``m``: a flow.
    It is zero except in the last month of each tax year, when the year's
    dividends are taxed, and it is paid out of the account.
    """

    balances: list[float]
    cost_bases: list[float]
    dividend_taxes: list[float]


def compute_market_account_schedule(
    opening_balance: float,
    opening_cost_basis: float,
    monthly_deposits: list[float],
    taxable_income_before_dividends_by_year: list[TaxableAmounts],
    market_config: MarketConfig,
    tax_module: TaxModule,
) -> MarketAccountSchedule:
    """Project a market account that grows, takes deposits, and pays dividend tax.

    Each month the account grows at ``market_config``'s return rate, dividends
    included, and then takes that month's deposit. Nothing is ever withdrawn
    except the tax on dividends.

    Dividends are never added to the account: they are already part of the
    growth. What this works out is how much of that growth was paid out as
    dividends, because those are taxed every year instead of when the account is
    sold. At the end of each tax year the year's dividends are taxed at the
    long-term capital gains rates (they are assumed to be qualified), the tax is
    taken out of the account, and what is left of them counts toward the basis,
    so it is not taxed a second time at the sale.

    Args:
        opening_balance: the account's balance at the start of month 0.
        opening_cost_basis: its cost basis at the same moment.
        monthly_deposits: the dollars paid in during each month, one per month
            of the projection, month 0 through the last month inclusive. A
            deposit made in month ``m`` is first seen in ``balances[m + 1]``, so
            the last month's deposit never appears in the result: there is no
            month after it to show it in.
        taxable_income_before_dividends_by_year: for each tax year in order, the
            rest of that year's taxable income, which the dividends are taxed on
            top of. Which long-term capital gains rate applies depends on it,
            because the rest of the year's income fills the lower brackets first.
            One per year that ends inside the projection.
        market_config: the market's return, and how much of it is dividends.
        tax_module: prices the dividend tax.
    """
    num_months = len(monthly_deposits) - 1
    num_year_ends = (num_months + 1) // MONTHS_PER_YEAR
    assert num_months >= 0
    assert opening_balance >= 0
    assert opening_cost_basis >= 0
    assert all(deposit >= 0 for deposit in monthly_deposits)
    assert len(taxable_income_before_dividends_by_year) == num_year_ends, (
        f"need one dividend tax base per tax year ({num_year_ends}), "
        f"got {len(taxable_income_before_dividends_by_year)}"
    )

    # NOTE: first value filled in; each pass appends the NEXT month's value
    balances = [opening_balance]
    cost_bases = [opening_cost_basis]
    dividend_taxes: list[float] = []
    # What the account earned since the last year end. Dividends are a share of
    # this, so it has to be accumulated as the year runs rather than inferred from
    # the balances, which also move on deposits.
    growth_this_year = 0.0

    for month, deposit in enumerate(monthly_deposits):
        grown = market_config.get_pretax_monthly_wealth(balances[-1], 1)[1]
        growth_this_year += grown - balances[-1]

        # Tax is settled annually, so it lands entirely in the last month of each
        # year and is zero in every other month.
        if month % MONTHS_PER_YEAR == MONTHS_PER_YEAR - 1:
            dividends = market_config.get_dividends_from_growth(growth_this_year)
            dividend_tax = tax_module.extra_tax_from(
                month,
                taxable_income_before_dividends_by_year[month // MONTHS_PER_YEAR],
                TaxableAmounts(long_term_capital_gains=dividends),
            ).long_term_capital_gain
            reinvested = round(dividends - dividend_tax, 2)
            growth_this_year = 0.0
        else:
            dividend_tax = 0.0
            reinvested = 0.0
        dividend_taxes.append(dividend_tax)

        balances.append(round(grown + deposit - dividend_tax, 2))
        cost_bases.append(round(cost_bases[-1] + deposit + reinvested, 2))

    # A balance is state at a point in time, so each list was seeded with month
    # 0's value and every pass appended the NEXT month's, leaving one entry too
    # many: the balance at the start of the month after the projection ends. The
    # taxes are flows, what happened DURING a month, so they are already the right
    # length.
    balances.pop()
    cost_bases.pop()
    return MarketAccountSchedule(
        balances=balances,
        cost_bases=cost_bases,
        dividend_taxes=dividend_taxes,
    )
