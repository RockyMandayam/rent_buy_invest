from dataclasses import dataclass

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.core.amortization import compute_loan_amortization_schedule
from rent_buy_invest.core.depreciation import compute_depreciation_schedule
from rent_buy_invest.core.mortgage_insurance import compute_mortgage_insurance_schedule
from rent_buy_invest.core.points_amortization import (
    compute_points_amortization_schedule,
)


@dataclass(frozen=True)
class RentalSaleResult:
    """What selling a rental property produces, in cash and in taxable gain.

    Two separate stories, the same split that runs through the monthly figures.

    The cash story is simple: you receive ``final_sale_price``, hand back both
    kinds of selling cost, and pay off whatever is left of the loan. What remains
    is ``pretax_cash_proceeds`` -- "pretax" because the tax owed on the sale is
    computed elsewhere, from the gain figures below, and subtracted by the caller.

    The taxable story runs through the basis. ``original_basis`` is what the
    property cost you: its purchase price plus the closing costs that count toward
    it. Every dollar of depreciation you deducted while holding it is a dollar of
    that cost you have already been given tax relief for, so it comes off, leaving
    ``adjusted_basis`` -- the part of your cost you have not yet recovered. Gain is
    measured against that, which is why depreciating raises the eventual gain by
    exactly what you deducted.

    That gain is then split, because its two halves are taxed at different rates:

    - ``depreciation_recapture_gain`` -- gain up to the depreciation you took,
      capped at a 25% rate. The IRS calls this unrecaptured section 1250 gain.
    - ``long_term_capital_gain`` -- everything above that, taxed at the ordinary
      long-term capital gains rates.

    Both are taxed; the split only decides the rate on each part.

    Those two always add up to ``total_gain`` -- but only when it is positive.

    ``total_gain`` is reported raw and **may be negative**, when the property sells
    for less than its adjusted basis. Then both ``depreciation_recapture_gain`` and
    ``long_term_capital_gain`` are zero, because a loss belongs in neither bucket:
    there is nothing to tax at either rate. The loss sits in ``total_gain`` alone,
    unallocated, and whether it is worth anything is deliberately left to whoever
    computes the tax rather than decided here.

    ``unamortized_discount_points`` sits outside both stories. Points are deducted
    a little at a time over the loan's term, and selling ends the loan early, so
    whatever is left undeducted can be taken in full in the year of the sale. It is
    an ordinary deduction against income, not part of the gain, so it is reported on
    its own rather than folded into either figure above.

    Nothing in this result is exempt from tax. When you sell a home you have lived
    in, the first $250,000 of gain is tax-free for a single filer -- but a property
    rented for its whole life never qualifies, so the whole gain here is taxable.
    """

    final_sale_price: float
    deductible_selling_costs: float
    nondeductible_selling_costs: float
    loan_payoff: float
    pretax_cash_proceeds: float

    unamortized_discount_points: float

    original_basis: float
    accumulated_depreciation: float
    adjusted_basis: float
    amount_realized: float
    total_gain: float
    depreciation_recapture_gain: float
    long_term_capital_gain: float


class RentalProperty:
    """A property owned purely to rent out, projected month by month.

    The property comes down to five monthly streams. Each one either moves money,
    changes what you are taxed on, or both:

    | stream              | money moves? | changes taxable income? |
    |---------------------|--------------|-------------------------|
    | rent received       | in           | yes                     |
    | operating expenses  | out          | yes                     |
    | mortgage interest   | out          | yes                     |
    | mortgage principal  | out          | **no**                  |
    | depreciation        | **no**       | yes                     |
    | discount points     | **no**       | yes                     |

    The last three are one-sided, and that is the whole point of this class.
    Principal leaves your account without being deductible -- it buys equity
    rather than paying for anything, so you still have the money, it is just in the
    house now. Depreciation is deductible even though no money moves at all. So are
    the discount points, whose cash left at closing and is counted among the upfront
    costs, but which a rental deducts a little at a time over the loan's term.

    So the two figures produced here are:

        cash flow      = rent - operating expenses - interest - principal
        taxable income = rent - operating expenses - interest - depreciation - discount points

    Both matter, for different reasons. Cash flow decides how much money is
    actually available to invest each month, which is what the tool compares
    between options and compounds to a final answer. Taxable income is not a
    destination -- it exists only to produce a tax bill, and that bill is itself
    cash, so it loops back into the cash figure. Depreciation is the clearest case:
    no money moves, but it shrinks the tax bill, so it puts real money in your
    pocket.

    Every list attribute is indexed by month and has length ``num_months + 1``
    (month 0 through month ``num_months`` inclusive), matching every other monthly
    projection in this tool.

    This models a property that is rented for the entire time it is held. A home
    you live in is not a rental: it earns no rent, is not depreciated, and is
    handled by ``Calculator`` instead.
    """

    def __init__(
        self,
        buy_config: BuyConfig,
        annual_inflation_rate: float,
        num_months: int,
    ) -> None:
        """
        Args:
            buy_config: Describes the property being rented out. Its
                ``rental_income_config`` must be set -- a config without one
                describes a home someone lives in, which is not a rental.
            annual_inflation_rate: General annual price inflation, as a fraction.
                Grows the inflation-linked holding costs (utilities, HOA,
                insurance, home warranty), and, where ``buy_config`` sets an
                assessment cap, the assessed value that property tax is charged
                on. Maintenance and management instead track the home's value,
                using the appreciation rate already in ``buy_config``.
            num_months: Last month of the projection; results cover month 0 through
                this month inclusive.
        """
        assert num_months > 0
        assert buy_config.rental_income_config is not None, (
            "A RentalProperty needs a buy_config with a rental_income_config; one "
            "without describes a home that is lived in, not rented out."
        )

        self.buy_config: BuyConfig = buy_config
        self.num_months: int = num_months

        self._amortization_schedule = compute_loan_amortization_schedule(
            buy_config.initial_loan_amount,
            buy_config.mortgage_annual_interest_rate,
            buy_config.get_monthly_mortgage_payment(),
            num_months,
        )
        mortgage_insurance_schedule = compute_mortgage_insurance_schedule(
            self._amortization_schedule,
            buy_config.is_fha_loan,
            buy_config.initial_loan_amount,
            buy_config.initial_loan_fraction,
            buy_config.purchase_price,
            buy_config.annual_mortgage_insurance_fraction,
            buy_config.home_appraisal_cost,
        )

        # Only the building depreciates, so the basis is the building's share of
        # what the property cost -- its price plus the closing costs that add to
        # basis. Land is excluded and never depreciates.
        self.depreciable_basis: float = (
            buy_config.rental_income_config.building_fraction_of_value
            * (
                buy_config.purchase_price
                + buy_config.get_part_of_basis_upfront_one_time_cost()
            )
        )
        self._depreciation_schedule = compute_depreciation_schedule(
            self.depreciable_basis, num_months
        )

        # Points bought down the interest rate and were paid at closing. A home you
        # live in deducts them that year; a rental spreads them over the loan term.
        self._points_amortization_schedule = compute_points_amortization_schedule(
            buy_config.mortgage_discount_points_fee_fraction
            * buy_config.initial_loan_amount,
            buy_config.mortgage_term_months,
            num_months,
        )

        self.monthly_loan_balance: list[
            float
        ] = self._amortization_schedule.starting_balances
        self.monthly_mortgage_interest: list[
            float
        ] = self._amortization_schedule.interest_payments
        self.monthly_mortgage_principal: list[
            float
        ] = self._amortization_schedule.principal_payments
        self.monthly_depreciation: list[
            float
        ] = self._depreciation_schedule.monthly_depreciation
        self.monthly_discount_points_deduction: list[
            float
        ] = self._points_amortization_schedule.monthly_deduction
        self.monthly_rental_income: list[float] = buy_config.get_monthly_rental_incomes(
            num_months
        )

        home_value_related_costs = buy_config.get_home_value_related_monthly_costs(
            annual_inflation_rate, num_months
        )
        inflation_related_costs = buy_config.get_inflation_related_monthly_costs(
            annual_inflation_rate, num_months
        )

        # The catch-all stream: property tax, homeowners and flood insurance, HOA,
        # owner-paid utilities, maintenance, management, home warranty, mortgage
        # insurance, and the one-off appraisal that ends PMI.
        #
        # What they have in common is that each behaves exactly one way -- money
        # leaves your account and the amount is deductible -- so both figures below
        # subtract the identical number. The mortgage is kept out because it does
        # not behave one way: its principal half is not deductible, so folding the
        # payment in here would wrongly shrink taxable income. Its interest half
        # would fit, but is tracked on its own so each figure can take exactly the
        # part it needs.
        #
        # Mortgage insurance belongs here even though it is not deductible for a
        # home you live in; for a rental it is an ordinary cost of doing business,
        # no different from the homeowners insurance beside it.
        self.monthly_operating_expenses: list[float] = [
            round(
                home_value_related_costs[month]
                + inflation_related_costs[month]
                + mortgage_insurance_schedule.premiums[month]
                + mortgage_insurance_schedule.appraisal_costs[month],
                2,
            )
            for month in range(num_months + 1)
        ]

        # What leaves your bank account for the mortgage: interest plus principal.
        self.monthly_mortgage_payment: list[float] = [
            round(
                self.monthly_mortgage_interest[month]
                + self.monthly_mortgage_principal[month],
                2,
            )
            for month in range(num_months + 1)
        ]

        # What happened to your bank account. Takes the whole mortgage payment,
        # since principal leaves your account too, and ignores depreciation, since
        # no money moves. Positive means the property paid for itself that month
        # and handed you the remainder; negative means you covered a shortfall out
        # of pocket. This is the figure the tool invests and compounds.
        self.monthly_pretax_cash_flow: list[float] = [
            round(
                self.monthly_rental_income[month]
                - self.monthly_operating_expenses[month]
                - self.monthly_mortgage_payment[month],
                2,
            )
            for month in range(num_months + 1)
        ]

        # What the property adds to the income you are taxed on. Mirror image of the
        # figure above: takes only the interest half of the mortgage, and does take
        # depreciation. Routinely negative even in a month the property handed you
        # money, which is exactly what makes depreciation worth having.
        self.monthly_taxable_income: list[float] = [
            round(
                self.monthly_rental_income[month]
                - self.monthly_operating_expenses[month]
                - self.monthly_mortgage_interest[month]
                - self.monthly_depreciation[month]
                - self.monthly_discount_points_deduction[month],
                2,
            )
            for month in range(num_months + 1)
        ]

    def accumulated_depreciation(self, through_month: int) -> float:
        """Total depreciation deducted from month 0 through ``through_month``.

        This is what reduces the property's cost basis when it is sold, and so what
        the depreciation recapture at sale is computed on.
        """
        return self._depreciation_schedule.accumulated_through(through_month)

    def sale(self, final_sale_price: float, month: int) -> RentalSaleResult:
        """Sell the property in ``month`` for ``final_sale_price``.

        ``month`` is a point in the projection, and the state read from it is
        start-of-month, matching how the rest of the tool reports a month: the loan
        payoff is the balance owed entering that month.

        Applies no rates. This reports the components; converting them into a tax
        bill belongs to whoever knows the brackets.
        """
        assert final_sale_price >= 0
        assert 0 <= month <= self.num_months

        original_basis = round(
            self.buy_config.purchase_price
            + self.buy_config.get_part_of_basis_upfront_one_time_cost(),
            2,
        )
        accumulated_depreciation = self.accumulated_depreciation(month)
        adjusted_basis = round(original_basis - accumulated_depreciation, 2)

        # Only the deductible costs come off the amount realized; the rest are
        # money out of your pocket that the gain calculation simply ignores.
        deductible_selling_costs = round(
            self.buy_config.get_deductible_selling_costs(final_sale_price), 2
        )
        nondeductible_selling_costs = round(
            self.buy_config.get_nondeductible_selling_costs(final_sale_price), 2
        )
        amount_realized = round(final_sale_price - deductible_selling_costs, 2)

        # Reported raw: negative when the property sold for less than the part of
        # its cost you had not yet deducted.
        total_gain = round(amount_realized - adjusted_basis, 2)
        if total_gain <= 0:
            # nothing gained, so nothing to recapture and nothing to tax
            depreciation_recapture_gain = 0.0
            long_term_capital_gain = 0.0
        else:
            depreciation_recapture_gain = round(
                min(total_gain, accumulated_depreciation), 2
            )
            long_term_capital_gain = round(total_gain - depreciation_recapture_gain, 2)

        # selling ends the loan, so the points not yet deducted are deductible now
        unamortized_discount_points = (
            self._points_amortization_schedule.unamortized_remainder_after(month)
        )

        loan_payoff = self._amortization_schedule.starting_balances[month]
        pretax_cash_proceeds = round(
            final_sale_price
            - deductible_selling_costs
            - nondeductible_selling_costs
            - loan_payoff,
            2,
        )

        return RentalSaleResult(
            final_sale_price=final_sale_price,
            deductible_selling_costs=deductible_selling_costs,
            nondeductible_selling_costs=nondeductible_selling_costs,
            loan_payoff=loan_payoff,
            pretax_cash_proceeds=pretax_cash_proceeds,
            unamortized_discount_points=unamortized_discount_points,
            original_basis=original_basis,
            accumulated_depreciation=accumulated_depreciation,
            adjusted_basis=adjusted_basis,
            amount_realized=amount_realized,
            total_gain=total_gain,
            depreciation_recapture_gain=depreciation_recapture_gain,
            long_term_capital_gain=long_term_capital_gain,
        )
