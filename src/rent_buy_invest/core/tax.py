from dataclasses import dataclass

from rent_buy_invest.configs.market_config import MarketConfig

# Gain that comes from depreciation you already deducted is taxed at your ordinary
# rate, but never above this. Someone in the 37% bracket hands back the deductions
# at 25%; someone in the 12% bracket hands them back at 12%. That gap, plus the
# years between deducting and repaying, is the entire benefit of depreciating.
MAX_DEPRECIATION_RECAPTURE_RATE = 0.25


@dataclass(frozen=True)
class LiquidationTax:
    """Tax owed on the sale of a property, split by what is being taxed.

    ``total`` is what you actually pay; the two parts above it show where it came
    from and are reported separately because they are charged at different rates.
    """

    depreciation_recapture_tax: float
    long_term_capital_gain_tax: float
    total: float


class TaxModule:
    """Turns amounts of income and gain into dollars of tax owed.

    A thin layer over ``MarketConfig``, which holds the brackets and knows how to
    apply them. What this adds is the rules specific to owning a rental: that a
    loss offsets other income, that gain from depreciation is capped at
    ``MAX_DEPRECIATION_RECAPTURE_RATE``, and the order the two kinds of gain stack
    in at sale.

    Everything here is a rate question. Deciding *what* the amounts are belongs to
    ``RentalProperty``; this decides what they cost.
    """

    def __init__(self, market_config: MarketConfig) -> None:
        self.market_config: MarketConfig = market_config

    def annual_rental_activity_tax(
        self,
        month: int,
        base_ordinary_income: float,
        taxable_rental_income: float,
    ) -> float:
        """Tax on a year of renting the property out, or the tax it saves you.

        A rental's taxable income is added to whatever else you earn, so it is
        taxed at your marginal rate rather than from the bottom bracket up. A
        negative figure -- routine, since depreciation is deducted without any
        money moving -- works the same way in reverse: it comes off your other
        income and saves tax at that same marginal rate.

        Returns a positive number for tax owed and a negative number for tax
        saved, so a caller can subtract it from cash flow either way.

        TODO: Known limitation: a loss can only offset income you actually have. In a
        year with no ordinary income -- retirement, in this tool -- a loss is worth
        nothing and is not carried forward to a later year, though real tax law
        would carry it.
        """
        assert month >= 0
        assert base_ordinary_income >= 0

        if taxable_rental_income >= 0:
            return round(
                self.market_config.get_additional_tax_from_additional_income(
                    month, base_ordinary_income, taxable_rental_income
                ),
                2,
            )
        tax_saved = round(
            self.market_config.get_income_tax_savings_from_deduction(
                month, base_ordinary_income, -taxable_rental_income
            ),
            2,
        )
        # guard against returning -0.0 when the loss was worth nothing
        # -0.0 is falsy in python
        return -tax_saved if tax_saved else 0.0

    def liquidation_tax(
        self,
        month: int,
        ordinary_income: float,
        depreciation_recapture_gain: float,
        long_term_capital_gain: float,
    ) -> LiquidationTax:
        """Tax owed in the year the property is sold.

        The two kinds of gain are not taxed independently -- they stack, in a fixed
        order, on top of the income you already have:

            ordinary income  ->  depreciation recapture  ->  capital gain

        Each layer starts where the one below it ended. Ignoring the order would
        understate the capital gains rate, most severely in a low-income year,
        which is exactly when a sale is most likely to be modeled here.

        Only the ceiling differs between the layers: recapture is charged at your
        ordinary rates but never above ``MAX_DEPRECIATION_RECAPTURE_RATE``, while
        the capital gain uses the long-term capital gains brackets.

        TODO: A sale at a loss reaches this method as two zeros and is therefore untaxed.
        Whether such a loss ought to produce a deduction is a separate question
        this tool does not yet answer.
        """
        assert month >= 0
        assert ordinary_income >= 0
        assert depreciation_recapture_gain >= 0
        assert long_term_capital_gain >= 0

        # First layer above ordinary income: what the recapture would cost at
        # ordinary rates, then capped. Note that depreciation recapture is taxed
        # at ORDINARY not Long Term Cap Gains rate, capped at MAX_DEPRECIATION_RECAPTURE_RATE
        recapture_tax_at_ordinary_rates = (
            self.market_config.get_additional_tax_from_additional_income(
                month, ordinary_income, depreciation_recapture_gain
            )
        )
        depreciation_recapture_tax = round(
            min(
                MAX_DEPRECIATION_RECAPTURE_RATE * depreciation_recapture_gain,
                recapture_tax_at_ordinary_rates,
            ),
            2,
        )

        # Second layer: capital gain starts where the recapture ended. Taking the
        # difference of two calls isolates the capital gains tax, since the tax on
        # the base is identical in both and cancels.
        capital_gain_starts_at = ordinary_income + depreciation_recapture_gain
        long_term_capital_gain_tax = round(
            self.market_config.get_tax(
                month,
                capital_gain_starts_at,
                long_term_capital_gains=long_term_capital_gain,
            )
            - self.market_config.get_tax(month, capital_gain_starts_at),
            2,
        )

        return LiquidationTax(
            depreciation_recapture_tax=depreciation_recapture_tax,
            long_term_capital_gain_tax=long_term_capital_gain_tax,
            total=round(depreciation_recapture_tax + long_term_capital_gain_tax, 2),
        )
