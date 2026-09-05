from dataclasses import dataclass

from rent_buy_invest.configs.market_config import MarketConfig

# Gain that comes from depreciation you already deducted is taxed at your ordinary
# rate, but never above this. Someone in the 37% bracket hands back the deductions
# at 25%; someone in the 12% bracket hands them back at 12%. That gap, plus the
# years between deducting and repaying, is the entire benefit of depreciating.
MAX_DEPRECIATION_RECAPTURE_RATE = 0.25


@dataclass(frozen=True)
class RealizedGainsTax:
    """The extra tax from realizing gains in a year, split by what is being taxed.

    ``total`` is the extra tax the gains caused -- not a whole tax bill. The tax
    on the income you would have earned anyway is excluded, because it is the same
    whichever choice you make. The parts above it show where the figure came from:
    the two gains are charged at different rates, and any deduction against ordinary
    income comes off the whole thing.

        total = depreciation_recapture_tax + long_term_capital_gain_tax
                - tax_saved_by_deduction

    ``tax_saved_by_deduction`` is positive, like every saving in this class, so it
    subtracts. ``total`` can come out negative when the deduction is worth more
    than the gains cost.
    """

    depreciation_recapture_tax: float
    long_term_capital_gain_tax: float
    tax_saved_by_deduction: float
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

    def annual_dividend_tax(
        self,
        month: int,
        base_ordinary_income: float,
        dividends: float,
    ) -> float:
        """Tax on a year of dividends from a taxable brokerage account.

        Returns a positive number: the tax owed, in dollars, for that year alone.
        It is the EXTRA tax the dividends cause, stacked on top of whatever else
        was earned, for the same reason every other figure in this class is a
        difference -- the tax on the rest of your income is identical in both
        worlds and cancels.

        ``base_ordinary_income`` is what the year's earlier layers left, not your
        salary. A rental running a loss drags taxable income down before the
        dividends land on it, so passing salary here would tax them in a bracket
        they never reach. The caller is responsible for that ordering today;
        ``annual_rental_activity_tax`` is the layer that comes before this one.

        Dividends are assumed to be entirely QUALIFIED, so they are taxed at the
        long-term capital gains brackets rather than as ordinary income. That is
        right for a broad stock index fund and too generous for a REIT, a bond
        fund, or many foreign funds, whose distributions are largely ordinary.
        """
        assert month >= 0
        assert base_ordinary_income >= 0
        assert dividends >= 0

        return round(
            self.market_config.get_tax(
                month, base_ordinary_income, long_term_capital_gains=dividends
            )
            - self.market_config.get_tax(month, base_ordinary_income),
            2,
        )

    def tax_saved_by_deduction(
        self,
        month: int,
        ordinary_income: float,
        deduction: float,
    ) -> float:
        """How much a deduction against ordinary income cuts the tax bill.

        Returns a **positive** number: the amount you no longer owe. That is the
        opposite convention from the rest of this class, where positive means tax
        owed, and it is deliberate -- a caller subtracts a saving, and a figure
        called a saving should not be negative.

        A deduction can only offset income you actually have. Deducting more than
        you earned saves only what the income was worth, and the remainder is not
        carried into another year.
        """
        assert month >= 0
        assert ordinary_income >= 0
        assert deduction >= 0

        return round(
            self.market_config.get_income_tax_savings_from_deduction(
                month, ordinary_income, deduction
            ),
            2,
        )

    def tax_on_realized_gains(
        self,
        month: int,
        ordinary_income: float,
        depreciation_recapture_gain: float,
        long_term_capital_gain: float,
        ordinary_income_deduction: float = 0,
    ) -> RealizedGainsTax:
        """The extra tax caused by realizing gains in a year.

        Not a whole tax bill and not specific to property: it takes gains and a
        deduction and returns what they cost. The investing world calls it with no
        property at all.

        **What is taxable, by category.** Income is not one pile. Each category has
        its own rate schedule:

        ==========================================  ===============================
        category                                    schedule
        ==========================================  ===============================
        ordinary income, less deductions            ordinary brackets
        (salary, rent, short-term capital gains)
        depreciation recapture                      ordinary rates, capped at
                                                    ``MAX_DEPRECIATION_RECAPTURE_RATE``
        long-term capital gain                      long-term capital gains brackets
        ==========================================  ===============================

        Deductions come off ordinary income, which is the bottom of the pile. That
        is why ``ordinary_income_deduction`` is a parameter here rather than
        something a caller nets out first -- see below.

        **The categories are not independent.** Each one stacks on top of the ones
        beneath it, and its *rate* depends on how much is down there:

            ordinary income  (less any deduction)
              ->  depreciation recapture
                ->  long-term capital gain

        A long-term gain is always charged on its own schedule -- it never becomes
        ordinary income -- but your salary has already used up the lower bands, so
        the gain starts further up. The same $100,000 gain can cost 5% or 15%
        depending only on what sits below it. Handing a caller the job of
        sequencing that would be easy to get wrong, so it happens here: the
        deduction comes off first, then each layer is charged where it lands.

        **Why a difference and not a total.** The tax on your salary is owed
        whether or not you sell anything, so it is identical in both worlds this
        tool compares and cancels out of the answer. Charging it would also make
        each world's wealth meaningless on its own -- income tax on a job has no
        business being subtracted from the proceeds of selling a house. So the whole
        year is worked out the way the law does it, and then what would have been
        owed anyway is subtracted:

            total = (ordinary + recapture + capital gain, all stacked)
                    - (ordinary alone, with no sale and no deduction)

        ``ordinary_income`` is therefore a *position*, not a charge: it says where
        on the brackets everything else lands. It is never taxed here.

        TODO: A sale at a loss reaches this method as two zeros and is therefore
        untaxed. Whether such a loss ought to produce a deduction is a separate
        question this tool does not yet answer.
        """
        assert month >= 0
        assert ordinary_income >= 0
        assert depreciation_recapture_gain >= 0
        assert long_term_capital_gain >= 0
        assert ordinary_income_deduction >= 0

        tax_saved_by_deduction = self.tax_saved_by_deduction(
            month, ordinary_income, ordinary_income_deduction
        )
        # everything above stacks on what is left of the income
        ordinary_income = max(ordinary_income - ordinary_income_deduction, 0)

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

        return RealizedGainsTax(
            depreciation_recapture_tax=depreciation_recapture_tax,
            long_term_capital_gain_tax=long_term_capital_gain_tax,
            tax_saved_by_deduction=tax_saved_by_deduction,
            total=round(
                depreciation_recapture_tax
                + long_term_capital_gain_tax
                - tax_saved_by_deduction,
                2,
            ),
        )
