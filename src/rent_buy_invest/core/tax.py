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


@dataclass(frozen=True)
class TaxableAmounts:
    """What happened in one tax year, sorted into the categories taxed differently.

    Dollars of income, deduction and gain -- not tax. There are four fields
    because this tool taxes four things by different rules; anything a caller has
    is one of them, and where each lands is fixed law rather than a caller's
    choice:

        ordinary income, less deductions   ordinary brackets
          -> depreciation recapture        ordinary rates, capped at
                                           MAX_DEPRECIATION_RECAPTURE_RATE
            -> long-term capital gain      long-term capital gains brackets

    Within a category the items are interchangeable: a year's rent and a year's
    salary are one number by the time the brackets see them, and so are a
    mortgage interest deduction and a rental loss. Between categories they are
    not, which is why the split is here and not finer.

    Amounts add, so a year can be built up a piece at a time and priced once.
    """

    ordinary_income: float = 0.0
    ordinary_deductions: float = 0.0
    depreciation_recapture: float = 0.0
    long_term_capital_gains: float = 0.0

    def __add__(self, other: "TaxableAmounts") -> "TaxableAmounts":
        return TaxableAmounts(
            ordinary_income=self.ordinary_income + other.ordinary_income,
            ordinary_deductions=self.ordinary_deductions + other.ordinary_deductions,
            depreciation_recapture=(
                self.depreciation_recapture + other.depreciation_recapture
            ),
            long_term_capital_gains=(
                self.long_term_capital_gains + other.long_term_capital_gains
            ),
        )


@dataclass(frozen=True)
class TaxCost:
    """What some amounts cost, split by the schedule that charged each part.

    Each field is the EXTRA tax that category caused, in dollars, on top of what
    was already there -- never a whole tax bill. ``ordinary`` is income net of
    deductions, so it comes out negative in a year the deductions win, which is
    routine for a rental.

        total = ordinary + depreciation_recapture + long_term_capital_gain

    The split is by category and no finer. Attributing one category's tax to the
    individual items inside it -- how much of a year's ordinary tax was "the
    rent" versus "the mortgage interest" -- has no answer in tax law; only their
    combined effect is a fact.
    """

    ordinary: float
    depreciation_recapture: float
    long_term_capital_gain: float
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

    def _tax_owed(self, month: int, amounts: TaxableAmounts) -> float:
        """The whole tax bill for a year described by ``amounts``, in dollars.

        Private because an absolute bill is never what this tool wants: the tax
        on income you would have earned anyway is identical in both worlds being
        compared and cancels out of the answer. Charging it would also make each
        world's wealth meaningless on its own. Callers want ``extra_tax_from``,
        which is the difference of two of these.

        The categories are charged in the order they stack, each starting where
        the one beneath it ended.
        """
        taxable_ordinary_income = max(
            amounts.ordinary_income - amounts.ordinary_deductions, 0.0
        )
        tax = self.market_config.get_tax(
            month,
            amounts.ordinary_income,
            ordinary_income_deduction=amounts.ordinary_deductions,
        )

        # Recapture is charged at ordinary rates, but never above the cap.
        tax += min(
            MAX_DEPRECIATION_RECAPTURE_RATE * amounts.depreciation_recapture,
            self.market_config.get_additional_tax_from_additional_income(
                month, taxable_ordinary_income, amounts.depreciation_recapture
            ),
        )

        # Capital gain has its own schedule, but starts where the recapture ended:
        # the same gain costs more with more sitting underneath it.
        gains_start_at = taxable_ordinary_income + amounts.depreciation_recapture
        tax += self.market_config.get_tax(
            month,
            gains_start_at,
            long_term_capital_gains=amounts.long_term_capital_gains,
        ) - self.market_config.get_tax(month, gains_start_at)
        return tax

    def extra_tax_from(
        self, month: int, already: TaxableAmounts, added: TaxableAmounts
    ) -> TaxCost:
        """What ``added`` costs on top of ``already``, split by category.

        This is the one place tax layers are sequenced. Each category is priced
        where it actually lands -- on top of everything beneath it, including
        whatever ``added`` itself put there -- by pricing the same year three
        times and taking the steps between. The parts therefore add up to the
        total by construction, not by convention.

        Working a category out from ``already`` alone instead would charge it as
        if the other categories had not happened, and price some of it in
        brackets the year never reaches. That mistake is silent: it only shows up
        in years where an amount is big enough to move a bracket.

        ``already`` says where on the brackets everything lands; its own tax is
        never charged.
        """
        assert month >= 0
        assert already.ordinary_income >= 0
        assert added.ordinary_income >= 0
        assert added.ordinary_deductions >= 0
        assert added.depreciation_recapture >= 0
        assert added.long_term_capital_gains >= 0

        through_ordinary = already + TaxableAmounts(
            ordinary_income=added.ordinary_income,
            ordinary_deductions=added.ordinary_deductions,
        )
        through_recapture = through_ordinary + TaxableAmounts(
            depreciation_recapture=added.depreciation_recapture
        )
        through_gains = through_recapture + TaxableAmounts(
            long_term_capital_gains=added.long_term_capital_gains
        )

        tax_before = self._tax_owed(month, already)
        tax_through_ordinary = self._tax_owed(month, through_ordinary)
        tax_through_recapture = self._tax_owed(month, through_recapture)
        tax_through_gains = self._tax_owed(month, through_gains)

        ordinary = round(tax_through_ordinary - tax_before, 2)
        depreciation_recapture = round(tax_through_recapture - tax_through_ordinary, 2)
        long_term_capital_gain = round(tax_through_gains - tax_through_recapture, 2)
        return TaxCost(
            ordinary=ordinary,
            depreciation_recapture=depreciation_recapture,
            long_term_capital_gain=long_term_capital_gain,
            # the sum of the rounded parts, so the object is self-consistent
            total=round(ordinary + depreciation_recapture + long_term_capital_gain, 2),
        )

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
        # A profit is more ordinary income; a loss is a deduction against it.
        return self.extra_tax_from(
            month,
            TaxableAmounts(ordinary_income=base_ordinary_income),
            TaxableAmounts(
                ordinary_income=max(taxable_rental_income, 0.0),
                ordinary_deductions=max(-taxable_rental_income, 0.0),
            ),
        ).ordinary

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
        return self.extra_tax_from(
            month,
            TaxableAmounts(ordinary_income=base_ordinary_income),
            TaxableAmounts(long_term_capital_gains=dividends),
        ).long_term_capital_gain

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
        cost = self.extra_tax_from(
            month,
            TaxableAmounts(ordinary_income=ordinary_income),
            TaxableAmounts(ordinary_deductions=deduction),
        ).ordinary
        # a saving is the negative of a cost; guard against handing back -0.0,
        # which is falsy in python, when the deduction was worth nothing
        return -cost if cost else 0.0

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
        cost = self.extra_tax_from(
            month,
            TaxableAmounts(ordinary_income=ordinary_income),
            TaxableAmounts(
                ordinary_deductions=ordinary_income_deduction,
                depreciation_recapture=depreciation_recapture_gain,
                long_term_capital_gains=long_term_capital_gain,
            ),
        )
        depreciation_recapture_tax = cost.depreciation_recapture
        long_term_capital_gain_tax = cost.long_term_capital_gain
        # The deduction is the only ordinary-category amount here, so this
        # category's cost IS what the deduction did -- reported as a positive
        # saving, which is the opposite sign to the cost it came from.
        tax_saved_by_deduction = -cost.ordinary if cost.ordinary else 0.0

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
