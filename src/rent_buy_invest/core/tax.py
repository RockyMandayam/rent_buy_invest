from dataclasses import dataclass

from rent_buy_invest.configs.market_config import MarketConfig

# Gain that comes from depreciation you already deducted is taxed at your ordinary
# rate, but never above this. Someone in the 37% bracket hands back the deductions
# at 25%; someone in the 12% bracket hands them back at 12%. That gap, plus the
# years between deducting and repaying, is the entire benefit of depreciating.
MAX_DEPRECIATION_RECAPTURE_RATE = 0.25


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
    apply them. What this adds is the rules that sit above the brackets: that a
    loss offsets other income, that gain from depreciation is charged at ordinary
    rates but capped at ``MAX_DEPRECIATION_RECAPTURE_RATE``, and the order the
    categories stack in.

    There is one way in, ``extra_tax_from``. Every kind of tax this tool charges
    -- a year of rent, a year of dividends, a deduction, a sale -- is the same
    question asked with different amounts, so there is one method rather than one
    per occasion, and no call site gets to decide what stacks on what.

    Everything here is a rate question. Deciding *what* the amounts are belongs to
    ``RentalProperty``, ``Calculator`` and the experiments; this decides what they
    cost.
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
