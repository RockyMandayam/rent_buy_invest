import datetime

import pandas as pd

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.core.final_state import RentalVsInvestFinalState
from rent_buy_invest.core.initial_state import RentalVsInvestInitialState
from rent_buy_invest.core.rental_property import RentalProperty
from rent_buy_invest.core.tax import TaxModule
from rent_buy_invest.utils.data_utils import to_df
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR, increment_month


class RentalVsInvestExperiment:
    """Projects buying a property to rent out against investing the same money.

    Two worlds, month by month. In one you buy the property; in the other you put
    what it would have cost you into the market instead. Where you live does not
    appear anywhere: it is the same in both worlds, so it cancels out of the
    difference between them, which is the only thing this projects.

    **Upfront**, buying costs the down payment plus the one-time costs of closing.
    The investing world starts with exactly that amount in the market, and the
    buying world starts with nothing invested but property equity instead.

    **Each month**, the property produces cash after tax -- sometimes positive,
    sometimes negative. The investing world owns no property, so it produces no
    cash of its own. The entire difference between the two worlds is therefore
    just whatever the property did, which is what ``buy_surplus`` holds: positive
    when owning it left you better off that month, negative when it cost you.

    Whichever world came out ahead deposits that amount into its own investment
    account. Separately, both accounts compound at the market rate every month,
    whether or not either received a deposit.

    Tax is settled once a year rather than monthly, matching the rest of this
    tool. A rental that runs at a loss -- routine, since depreciation is deducted
    without any money moving -- produces a negative tax, which is money back and
    so raises ``buy_surplus``.

    The projection stops at the horizon without selling anything. Liquidating the
    property and comparing final wealth is a separate step.

    **Constructing this runs it.** The monthly loop happens once, at construction,
    and its results are stored as plain lists indexed by month. There is no method
    to call in the right order, and nothing downstream reads numbers back out of
    the rendered table. ``get_projection_df`` only formats what is already there.

    Named an experiment rather than a calculator because that is what it is: a
    completed run. The repo already uses the word that way -- ``ExperimentConfig``
    holds a run's inputs and ``ExperimentWriter`` writes its outputs -- but until
    now nothing was one, and ``main.py`` played that role procedurally.
    """

    def __init__(
        self,
        buy_config: BuyConfig,
        market_config: MarketConfig,
        personal_config: PersonalConfig,
        num_years: int,
        start_date: datetime.date,
    ) -> None:
        assert num_years > 0
        self.buy_config: BuyConfig = buy_config
        self.market_config: MarketConfig = market_config
        self.personal_config: PersonalConfig = personal_config
        self.num_years: int = num_years
        self.start_date: datetime.date = start_date

        self.num_months: int = num_years * MONTHS_PER_YEAR
        self.rental_property: RentalProperty = RentalProperty(
            buy_config, market_config.annual_inflation_rate, self.num_months
        )
        self.tax_module: TaxModule = TaxModule(market_config)

        # What buying costs you on day one, and therefore what the investing world
        # has to put in the market instead.
        self.upfront_cost_of_buying: float = round(
            buy_config.down_payment + buy_config.get_upfront_one_time_cost(), 2
        )
        # Stored rather than recomputed: both the monthly loop and the sale need
        # it, and they must agree on the final year's figure.
        self.ordinary_incomes: list[float] = personal_config.get_ordinary_incomes(
            self.num_months
        )

        # NOTE _project adds a bunch of instance attributes
        self.initial_state: RentalVsInvestInitialState = RentalVsInvestInitialState(
            upfront_one_time_cost_if_buying=round(
                buy_config.get_upfront_one_time_cost(), 2
            ),
            property_equity_if_buying=round(buy_config.down_payment, 2),
            market_balance_if_investing=self.upfront_cost_of_buying,
        )

        self._project()
        self.final_state: RentalVsInvestFinalState = self._liquidate()

    def _project(self) -> None:
        """Run the month-by-month projection, storing the result on the instance.

        Called once at construction. Everything it produces is a plain list
        indexed by month, so nothing downstream has to read numbers back out of
        the rendered DataFrame.
        """
        num_months = self.num_months
        rental_property = self.rental_property

        ordinary_incomes = self.ordinary_incomes
        property_values = self.buy_config.get_monthly_home_values(num_months)

        annual_taxes: list[float] = []
        dividend_taxes_if_buying: list[float] = []
        dividend_taxes_if_investing: list[float] = []
        buy_surpluses: list[float] = []
        after_tax_cash_flows: list[float] = []
        equities: list[float] = []
        # NOTE: first value filled in; the value at the start of each month
        invested_if_buying = [0.0]
        invested_if_investing = [self.upfront_cost_of_buying]
        # Cost basis: every dollar deposited, which is not gain when the account is
        # cashed out. Tracked alongside the balances, and popped the same way, so
        # the two cannot fall out of step.
        basis_if_buying = [0.0]
        basis_if_investing = [self.upfront_cost_of_buying]
        # What each account earned since the last year boundary. Dividends are a
        # share of this, so it has to be accumulated as the year runs rather than
        # inferred from the balances, which also move on deposits.
        growth_if_buying_this_year = 0.0
        growth_if_investing_this_year = 0.0

        for month in range(num_months + 1):
            # Both accounts grow for the month. This runs before tax because the
            # year's dividends are a share of this growth, and the tax on them
            # stacks on top of the rental's income for the same year.
            grown_if_buying = self.market_config.get_pretax_monthly_wealth(
                invested_if_buying[-1], 1
            )[1]
            grown_if_investing = self.market_config.get_pretax_monthly_wealth(
                invested_if_investing[-1], 1
            )[1]
            growth_if_buying_this_year += grown_if_buying - invested_if_buying[-1]
            growth_if_investing_this_year += (
                grown_if_investing - invested_if_investing[-1]
            )

            # Tax is settled annually, so it lands entirely in the last month of
            # each year and is zero in every other month.
            is_year_boundary = month % MONTHS_PER_YEAR == (MONTHS_PER_YEAR - 1)
            if is_year_boundary:
                income_for_the_year = sum(
                    ordinary_incomes[month + 1 - MONTHS_PER_YEAR : month + 1]
                )
                taxable_rental_income_for_the_year = sum(
                    rental_property.monthly_taxable_income[
                        month + 1 - MONTHS_PER_YEAR : month + 1
                    ]
                )
                # Dividends are already sitting in each balance -- an account
                # compounds at the total return, dividends included -- so this
                # only says how much of that growth is taxable now rather than
                # deferred to the sale.
                get_dividends = self.market_config.get_dividends_from_growth
                dividends_if_buying = get_dividends(growth_if_buying_this_year)
                dividends_if_investing = get_dividends(growth_if_investing_this_year)

                # One call per world, so a world's layers are charged in order
                # instead of each being worked out from salary in isolation. The
                # investing world owns no property, so it has no rental layer.
                annual_tax = self.tax_module.annual_rental_activity_tax(
                    month, income_for_the_year, taxable_rental_income_for_the_year
                )
                # Dividends are charged on top of what the rental left, not on
                # salary: a rental loss drags taxable income down first, and a
                # loss bigger than the income leaves nothing to stack on. The
                # investing world owns no property, so its base is just salary.
                dividend_tax_if_buying = self.tax_module.annual_dividend_tax(
                    month,
                    max(income_for_the_year + taxable_rental_income_for_the_year, 0.0),
                    dividends_if_buying,
                )
                dividend_tax_if_investing = self.tax_module.annual_dividend_tax(
                    month, income_for_the_year, dividends_if_investing
                )
                reinvested_if_buying = round(
                    dividends_if_buying - dividend_tax_if_buying, 2
                )
                reinvested_if_investing = round(
                    dividends_if_investing - dividend_tax_if_investing, 2
                )
                growth_if_buying_this_year = 0.0
                growth_if_investing_this_year = 0.0
            else:
                annual_tax = 0
                dividend_tax_if_buying = dividend_tax_if_investing = 0.0
                reinvested_if_buying = reinvested_if_investing = 0.0
            annual_taxes.append(annual_tax)
            dividend_taxes_if_buying.append(dividend_tax_if_buying)
            dividend_taxes_if_investing.append(dividend_tax_if_investing)

            # Positive tax is money owed, so it comes off what the property left
            # you with; negative tax is money back, so it adds.
            after_tax_cash_flow = round(
                rental_property.monthly_pretax_cash_flow[month] - annual_tax, 2
            )
            after_tax_cash_flows.append(after_tax_cash_flow)

            # How much better off the buying world was this month. The investing
            # world has no costs at all, so the whole difference is this figure.
            buy_surplus = after_tax_cash_flow
            buy_surpluses.append(buy_surplus)

            equities.append(
                round(
                    property_values[month]
                    - rental_property.monthly_loan_balance[month],
                    2,
                )
            )

            # Only the cheaper world has money spare to put in, so exactly one of
            # these is non-zero.
            deposit_if_buying = buy_surplus if buy_surplus >= 0 else 0.0
            deposit_if_investing = -buy_surplus if buy_surplus < 0 else 0.0

            # The dividend tax is paid out of the account, so it lowers the
            # balance and nothing else. The dividend left after that tax stays
            # invested and has already been taxed, so it is basis, not gain, when
            # the account is finally sold.
            invested_if_buying.append(
                round(grown_if_buying + deposit_if_buying - dividend_tax_if_buying, 2)
            )
            basis_if_buying.append(
                round(basis_if_buying[-1] + deposit_if_buying + reinvested_if_buying, 2)
            )
            invested_if_investing.append(
                round(
                    grown_if_investing
                    + deposit_if_investing
                    - dividend_tax_if_investing,
                    2,
                )
            )
            basis_if_investing.append(
                round(
                    basis_if_investing[-1]
                    + deposit_if_investing
                    + reinvested_if_investing,
                    2,
                )
            )

        # Only the balances are trimmed. A balance is state at a point in time, so
        # each was seeded with its month-0 value and every pass appended the NEXT
        # month's -- leaving one entry too many, the balance at the start of the
        # month after the horizon, which the projection does not cover. The other
        # lists hold flows, what happened DURING a month, so a pass appends its own
        # month and they come out the right length already.
        #
        # A consequence worth knowing: the final month's surplus is computed but
        # lands in the entry that gets discarded here, so it never moves a balance.
        # Reported month m is therefore the state entering month m, which is what
        # the sale at the horizon is priced against.
        invested_if_buying.pop()
        invested_if_investing.pop()
        basis_if_buying.pop()
        basis_if_investing.pop()

        self.invested_if_buying: list[float] = invested_if_buying
        self.invested_if_investing: list[float] = invested_if_investing
        self.basis_if_buying: list[float] = basis_if_buying
        self.basis_if_investing: list[float] = basis_if_investing
        self.property_values: list[float] = property_values
        self.equities: list[float] = equities
        self.annual_taxes: list[float] = annual_taxes
        self.dividend_taxes_if_buying: list[float] = dividend_taxes_if_buying
        self.dividend_taxes_if_investing: list[float] = dividend_taxes_if_investing
        self.after_tax_cash_flows: list[float] = after_tax_cash_flows
        self.buy_surpluses: list[float] = buy_surpluses

    def _liquidate(self) -> RentalVsInvestFinalState:
        """Sell the property and cash out both worlds, so wealth is comparable.

        Called once at construction, after the projection. An unsold property and
        an untaxed investment account are not comparable, so everything is turned
        into money here and the tax that would be owed on doing so is subtracted.

        The buying world's property gain and investment gain are taxed **together**
        rather than separately. Brackets are progressive, so two gains taxed apart
        cost less than the same total taxed as one, and this world realises both in
        the same year. ``main.py`` stacks them for the same reason.

        The sale is treated as happening in the tax year AFTER the projection ends,
        which is why the gains stack on the last projected year's salary alone and
        not on that year's rental income or dividends -- those were settled in
        their own year, at the year boundary, and are done with. It also means the
        rental earns no income in the year it is sold. A real sale lands mid-year,
        alongside part of a year of rent and a part-year of depreciation; that is
        not modelled, and the horizon is best read as "the end of the last full
        year of renting, sold the following January".
        """
        rental_property = self.rental_property
        sale = rental_property.sale(self.property_values[-1], self.num_months)

        # The bracket position everything stacks on is last year's income, and the
        # brackets themselves have inflated for the whole horizon by now.
        tax_month = self.num_months + 1
        # The same twelve months the monthly loop settled tax on at the final year boundary
        annual_income = sum(
            self.ordinary_incomes[self.num_months - MONTHS_PER_YEAR : self.num_months]
        )

        # Gains on the market accounts: the balance less what was put in. Basis is
        # every deposit, not just the opening one -- a world that paid in monthly
        # for thirty years is not taxed on the money it paid in. Losses are floored
        # at zero, since the tax layer has no way to use them yet.
        market_balance_if_buying = self.invested_if_buying[-1]
        market_balance_if_investing = self.invested_if_investing[-1]
        investment_gain_if_buying = max(
            market_balance_if_buying - self.basis_if_buying[-1], 0
        )
        investment_gain_if_investing = max(
            market_balance_if_investing - self.basis_if_investing[-1], 0
        )

        # Hand over what happened and let the tax layer work out what it costs.
        # Selling ended the loan, so the points never amortized are deductible in
        # full this year; tax_on_realized_gains knows that comes off before the gains
        # stack, so the ordering is not this method's business.
        tax_if_buying = self.tax_module.tax_on_realized_gains(
            tax_month,
            annual_income,
            sale.depreciation_recapture_gain,
            sale.long_term_capital_gain + investment_gain_if_buying,
            ordinary_income_deduction=sale.unamortized_discount_points,
        ).total

        # The investing world has no property, so no recapture and no deduction --
        # only the gain on its market account.
        tax_if_investing = self.tax_module.tax_on_realized_gains(
            tax_month, annual_income, 0, investment_gain_if_investing
        ).total

        return RentalVsInvestFinalState(
            market_balance_if_buying=market_balance_if_buying,
            sale_proceeds=sale.pretax_cash_proceeds,
            tax_if_buying=tax_if_buying,
            wealth_if_buying=round(
                market_balance_if_buying + sale.pretax_cash_proceeds - tax_if_buying, 2
            ),
            market_balance_if_investing=market_balance_if_investing,
            tax_if_investing=tax_if_investing,
            wealth_if_investing=round(
                market_balance_if_investing - tax_if_investing, 2
            ),
        )

    def get_projection_df(self) -> pd.DataFrame:
        """Render the stored projection as a table, for output."""
        rental_property = self.rental_property
        cols = {
            "Buy Rental: Invested (Pre-Tax)": self.invested_if_buying,
            "Buy Rental: Property Value": self.property_values,
            "Buy Rental: Loan Amount": rental_property.monthly_loan_balance,
            "Buy Rental: Equity": self.equities,
            "Buy Rental: Rental Income": rental_property.monthly_rental_income,
            "Buy Rental: Operating Expenses": rental_property.monthly_operating_expenses,
            "Buy Rental: Mortgage Interest Payment": rental_property.monthly_mortgage_interest,
            "Buy Rental: Mortgage Equity Payment": rental_property.monthly_mortgage_principal,
            "Buy Rental: Depreciation": rental_property.monthly_depreciation,
            "Buy Rental: Discount Points Deduction": rental_property.monthly_discount_points_deduction,
            "Buy Rental: Taxable Income": rental_property.monthly_taxable_income,
            "Buy Rental: Tax": self.annual_taxes,
            "Buy Rental: Cash Flow (After Tax)": self.after_tax_cash_flows,
            "Buy Rental: Dividend Tax": self.dividend_taxes_if_buying,
            "Buy Rental: Surplus": self.buy_surpluses,
            "Invest: Invested (Pre-Tax)": self.invested_if_investing,
            "Invest: Dividend Tax": self.dividend_taxes_if_investing,
        }
        rows = []
        date = self.start_date
        for _ in range(self.num_months + 1):
            rows.append(date.strftime("%b %d, %Y"))
            date = increment_month(date)
        return to_df(cols, rows, multi_col=True)
