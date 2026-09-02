from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.core.amortization import compute_loan_amortization_schedule
from rent_buy_invest.core.depreciation import compute_depreciation_schedule
from rent_buy_invest.core.mortgage_insurance import compute_mortgage_insurance_schedule


class RentalProperty:
    """A property owned purely to rent out, projected month by month.

    The property comes down to five monthly streams. Each one either moves money,
    changes what you are taxed on, or both:

    | stream             | money moves? | changes taxable income? |
    |--------------------|--------------|-------------------------|
    | rent received      | in           | yes                     |
    | operating expenses | out          | yes                     |
    | mortgage interest  | out          | yes                     |
    | mortgage principal | out          | **no**                  |
    | depreciation       | **no**       | yes                     |

    The last two are one-sided, and that is the whole point of this class.
    Principal leaves your account without being deductible -- it buys equity
    rather than paying for anything, so you still have the money, it is just in the
    house now. Depreciation is deductible even though no money moves at all.

    So the two figures produced here are different sums of the same five streams:

        cash flow      = rent - operating expenses - interest - principal
        taxable income = rent - operating expenses - interest - depreciation

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
            annual_inflation_rate: Rate at which the inflation-linked holding costs
                grow (utilities, HOA, insurance, home warranty). Property tax,
                maintenance, and management instead track the assessed value, using
                the rate already in ``buy_config``.
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
            buy_config.sale_price,
            buy_config.annual_mortgage_insurance_fraction,
            buy_config.home_appraisal_cost,
        )

        # Only the building depreciates, so the basis is the building's share of
        # what the property cost -- its price plus the closing costs that add to
        # basis. Land is excluded and never depreciates.
        self.depreciable_basis: float = (
            buy_config.rental_income_config.building_fraction_of_value
            * (
                buy_config.sale_price
                + buy_config.get_part_of_basis_upfront_one_time_cost()
            )
        )
        self._depreciation_schedule = compute_depreciation_schedule(
            self.depreciable_basis, num_months
        )

        self.monthly_mortgage_interest: list[
            float
        ] = self._amortization_schedule.interest_payments
        self.monthly_mortgage_principal: list[
            float
        ] = self._amortization_schedule.principal_payments
        self.monthly_depreciation: list[
            float
        ] = self._depreciation_schedule.monthly_depreciation
        self.monthly_rental_income: list[float] = buy_config.get_monthly_rental_incomes(
            num_months
        )

        home_value_related_costs = buy_config.get_home_value_related_monthly_costs(
            num_months
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
                - self.monthly_depreciation[month],
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
