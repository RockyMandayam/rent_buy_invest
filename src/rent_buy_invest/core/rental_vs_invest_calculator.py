import datetime

import pandas as pd

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.core.rental_property import RentalProperty
from rent_buy_invest.core.tax import TaxModule
from rent_buy_invest.utils.data_utils import to_df
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR, increment_month


class RentalVsInvestCalculator:
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

    def calculate(self) -> pd.DataFrame:
        num_months = self.num_months
        rental_property = self.rental_property

        ordinary_incomes = self.personal_config.get_ordinary_incomes(num_months)
        property_values = self.buy_config.get_monthly_home_values(num_months)

        annual_taxes: list[float] = []
        buy_surpluses: list[float] = []
        after_tax_cash_flows: list[float] = []
        equities: list[float] = []
        # NOTE: first value filled in; the value at the start of each month
        invested_if_buying = [0.0]
        invested_if_investing = [self.upfront_cost_of_buying]

        for month in range(num_months + 1):
            # Tax is settled annually, so it lands entirely in the last month of
            # each year and is zero in every other month.
            if month % MONTHS_PER_YEAR == (MONTHS_PER_YEAR - 1):
                annual_tax = self.tax_module.annual_rental_activity_tax(
                    month,
                    sum(ordinary_incomes[month + 1 - MONTHS_PER_YEAR : month + 1]),
                    sum(
                        rental_property.monthly_taxable_income[
                            month + 1 - MONTHS_PER_YEAR : month + 1
                        ]
                    ),
                )
            else:
                annual_tax = 0
            annual_taxes.append(annual_tax)

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

            # Both accounts grow for the month; the surplus goes to whichever
            # world actually had it.
            grown_if_buying = self.market_config.get_pretax_monthly_wealth(
                invested_if_buying[-1], 1
            )[1]
            grown_if_investing = self.market_config.get_pretax_monthly_wealth(
                invested_if_investing[-1], 1
            )[1]
            if buy_surplus >= 0:
                invested_if_buying.append(round(grown_if_buying + buy_surplus, 2))
                invested_if_investing.append(grown_if_investing)
            else:
                invested_if_buying.append(grown_if_buying)
                invested_if_investing.append(round(grown_if_investing - buy_surplus, 2))

        # Each list has one extra entry: the value at the start of the month after
        # the horizon, which the projection does not cover.
        invested_if_buying.pop()
        invested_if_investing.pop()

        cols = {
            "Buy Rental: Invested (Pre-Tax)": invested_if_buying,
            "Buy Rental: Property Value": property_values,
            "Buy Rental: Loan Amount": rental_property.monthly_loan_balance,
            "Buy Rental: Equity": equities,
            "Buy Rental: Rental Income": rental_property.monthly_rental_income,
            "Buy Rental: Operating Expenses": rental_property.monthly_operating_expenses,
            "Buy Rental: Mortgage Interest Payment": rental_property.monthly_mortgage_interest,
            "Buy Rental: Mortgage Equity Payment": rental_property.monthly_mortgage_principal,
            "Buy Rental: Depreciation": rental_property.monthly_depreciation,
            "Buy Rental: Discount Points Deduction": rental_property.monthly_discount_points_deduction,
            "Buy Rental: Taxable Income": rental_property.monthly_taxable_income,
            "Buy Rental: Tax": annual_taxes,
            "Buy Rental: Cash Flow (After Tax)": after_tax_cash_flows,
            "Buy Rental: Surplus": buy_surpluses,
            "Invest: Invested (Pre-Tax)": invested_if_investing,
        }
        rows = []
        date = self.start_date
        for _ in range(num_months + 1):
            rows.append(date.strftime("%b %d, %Y"))
            date = increment_month(date)
        return to_df(cols, rows, multi_col=True)
