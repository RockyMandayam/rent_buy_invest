from dataclasses import dataclass
from typing import Any

from rent_buy_invest.utils.data_utils import to_df


@dataclass(frozen=True)
class FinalState:
    wealth_if_renting: float
    wealth_if_buying: float

    def get_df(self) -> list[list[Any | None]]:
        rows = ["Wealth"]
        cols = {
            "Rent": [self.wealth_if_renting],
            "Buy": [self.wealth_if_buying],
        }
        return to_df(cols, rows)


@dataclass(frozen=True)
class RentalVsInvestFinalState:
    """What each world is worth after selling up at the horizon.

    ``wealth_if_buying`` and ``wealth_if_investing`` are the answer: the two
    numbers this whole comparison exists to produce. **Every other field is a
    building block** -- the arithmetic that got there, kept so the answer can be
    checked rather than taken on faith.

        wealth_if_buying    = market_balance_if_buying + sale_proceeds - tax_if_buying
        wealth_if_investing = market_balance_if_investing - tax_if_investing

    Two ways of having spent the same money: one bought a property to rent out,
    the other put that money in the market. Both are cashed out here so the
    comparison is like for like -- an unsold property and an untaxed investment
    account are not comparable wealth.

    ``market_balance_if_buying`` is money in the stock market, **not** the
    property. Buying a rental is itself an investment, so the distinction matters:
    the buying world ends up holding two assets, a market account and a property,
    and the property arrives separately as ``sale_proceeds``. The investing world
    holds only the one. That asymmetry is the whole comparison, and it is why the
    two equations above have a different number of terms.

    ``sale_proceeds`` is what the property nets after selling costs and paying off
    the loan. **It can be negative**, when what is still owed exceeds what the sale
    brings in; that is money brought to closing, and it reduces wealth like any
    other cost.

    ``tax_if_buying`` covers the whole sale year for that world: the depreciation
    handed back, the gain on the property, the gain on its investments, less the
    deduction for discount points that were never amortized because selling ended
    the loan early. It can be smaller than ``tax_if_investing`` even on a larger
    gain, since part of it is charged at the capped depreciation rate.
    """

    # building blocks: how the buying world reached its number.
    # It holds two assets -- a market account, and a property it sells.
    market_balance_if_buying: float
    sale_proceeds: float
    tax_if_buying: float
    # the answer, for the buying world
    wealth_if_buying: float

    # building blocks: how the investing world reached its number.
    # It holds one asset: a market account.
    market_balance_if_investing: float
    tax_if_investing: float
    # the answer, for the investing world
    wealth_if_investing: float

    def get_df(self) -> list[list[Any | None]]:
        rows = [
            "Market Account (Pre-Tax)",
            "Property Sale Proceeds",
            "Tax",
            "Wealth",
        ]
        cols = {
            "Buy Rental": [
                self.market_balance_if_buying,
                self.sale_proceeds,
                -self.tax_if_buying,
                self.wealth_if_buying,
            ],
            "Invest": [
                self.market_balance_if_investing,
                0,
                -self.tax_if_investing,
                self.wealth_if_investing,
            ],
        }
        return to_df(cols, rows)
