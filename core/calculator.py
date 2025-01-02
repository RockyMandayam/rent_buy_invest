import datetime

import pandas as pd

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils import math_utils
from rent_buy_invest.utils.data_utils import to_df

# This is the maximum mortgage amount as a fraction of the ORIGINAL home price
# for which the borrower does not have to pay PMI. When the mortgage amount falls
# to this amount, the borrower can request that the PMI be removed. As of today,
# Jan 25, 2024, this amount is 80%, and the lender is supposed to automatically
# remove the PMI at 78%.
MAXIMUM_MORTGAGE_AMOUNT_FRACTION_WITH_NO_PMI = 0.8


class Calculator:
    def __init__(
        self,
        house_config: HouseConfig,
        rent_config: RentConfig,
        market_config: MarketConfig,
        num_months: int,
        start_date: datetime.date,
        initial_state: InitialState,
    ) -> None:
        self.house_config: HouseConfig = house_config
        self.rent_config: RentConfig = rent_config
        self.market_config: MarketConfig = market_config
        self.num_months: int = num_months
        self.start_date: datetime.date = start_date
        self.initial_state: InitialState = initial_state

    def calculate(self) -> pd.DataFrame:
        # Some housing costs/gains can be calculated independently at once
        house_values = self.house_config.get_monthly_house_values(self.num_months)
        house_monthly_costs_related_to_house_value = (
            self.house_config.get_house_value_related_monthly_costs(self.num_months)
        )
        house_monthly_costs_related_to_inflation = (
            self.house_config.get_inflation_related_monthly_costs(
                self.rent_config.annual_rent_inflation_rate, self.num_months
            )
        )

        # Some renting costs/gains can be calculated independently at once
        rent_monthly_costs = self.rent_config.get_monthly_costs_of_renting(
            self.num_months
        )

        # The remaining housing and rental costs/gains are calculated in the loop
        # which projects forward month by month
        mortgage_interests = []
        paid_toward_equity = []
        mortgage_amounts = []
        equities = []
        pmis = []
        housing_monthly_surpluses = []
        rent_monthly_surpluses = []
        investment_values_if_renting = [
            self.initial_state.invested_in_market_if_renting
        ]  # NOTE: first value filled in
        investment_values_if_house = [0]  # NOTE: first value filed in

        mortgage_amount = self.house_config.initial_mortgage_amount
        monthly_mortgage_payment = self.house_config.get_monthly_mortgage_payment()
        for month in range(self.num_months + 1):
            mortgage_amounts.append(mortgage_amount)

            # mortgage interest cost
            mortgage_interest = round(
                mortgage_amount * self.house_config.mortgage_annual_interest_rate / 12,
                2,
            )
            mortgage_interests.append(mortgage_interest)

            # mortgage equity payment and equity value
            if mortgage_amount == 0:
                # mortage already paid off
                # no mortgage amount, so mortgage_interest is zero also
                toward_equity = 0
            elif mortgage_amount + mortgage_interest <= monthly_mortgage_payment:
                # final mortgage payment
                # paying interest on prev month and the remaining little mortgage amount
                toward_equity = mortgage_amount
            else:
                # regular mortgage payment
                toward_equity = round(monthly_mortgage_payment - mortgage_interest, 2)
            paid_toward_equity.append(toward_equity)
            equities.append(round(house_values[month] - mortgage_amount, 2))

            if (
                mortgage_amount
                <= MAXIMUM_MORTGAGE_AMOUNT_FRACTION_WITH_NO_PMI
                * self.house_config.sale_price
            ):
                pmi = 0
            else:
                pmi = round(
                    self.house_config.pmi_fraction
                    * self.house_config.initial_mortgage_amount,
                    2,
                )
            pmis.append(pmi)

            # monthly surplus from one option vs the other
            # investment_values_if_renting and investment_values_if_house have their
            # start-of-the-month value already filled in, so this calculates the value
            # at the end of the month.
            housing_monthly_payment = (
                house_monthly_costs_related_to_house_value[month]
                + house_monthly_costs_related_to_inflation[month]
                + mortgage_interest
                + toward_equity
                + pmi
            )
            rent_monthly_payment = rent_monthly_costs[month]
            gain_in_investment_if_renting = (
                self.market_config.get_pretax_monthly_wealth(
                    investment_values_if_renting[-1], 1
                )[1]
            )
            gain_in_investment_if_house = self.market_config.get_pretax_monthly_wealth(
                investment_values_if_house[-1], 1
            )[1]
            # Surplus from the perspective of renting
            surplus = round(housing_monthly_payment - rent_monthly_payment, 2)
            if surplus > 0:
                # if rent option has a relative surplus
                rent_monthly_surpluses.append(surplus)
                investment_values_if_renting.append(
                    round(gain_in_investment_if_renting + surplus, 2)
                )
                housing_monthly_surpluses.append(0)
                investment_values_if_house.append(gain_in_investment_if_house)
            elif surplus < 0:
                # if house option has a relative surplus
                # negate surplus to make it a positive from the perspective of housing
                surplus = -surplus
                rent_monthly_surpluses.append(0)
                investment_values_if_renting.append(gain_in_investment_if_renting)
                housing_monthly_surpluses.append(surplus)
                investment_values_if_house.append(
                    round(gain_in_investment_if_house + surplus, 2)
                )

            # update mortgage_amount for next iteration
            mortgage_amount -= toward_equity
            assert mortgage_amount >= 0, "Mortgage amount cannot be negative."
        # Pop last element from lists which have an extra item (starting value)
        investment_values_if_renting.pop()
        investment_values_if_house.pop()

        # RELIES on the fact that python dictionaries are now ordered
        cols = {
            # House: state
            "House: Non-house investment": investment_values_if_house,
            "House: House equity": equities,
            "House: Market value": house_values,
            "House: Mortgage amount": mortgage_amounts,
            # House: costs
            "House: Cost tied to market value": house_monthly_costs_related_to_house_value,
            "House: Cost tied to inflation": house_monthly_costs_related_to_inflation,
            "House: PMI": pmis,
            "House: Mortgage interest payment": mortgage_interests,
            "House: Mortgage equity payment": paid_toward_equity,
            # black formats the following line in an easy-to-misread way
            # fmt: off
            "House: Mortgage payment": [i + e for i, e in zip(mortgage_interests, paid_toward_equity)],
            # fmt: on
            # House: relative surplus
            "House: Surplus (vs renting)": housing_monthly_surpluses,
            # Rent: state
            "Rent: Investment": investment_values_if_renting,
            # Rent: costs
            "Rent: Cost tied to inflation": rent_monthly_costs,
            # Rent: relative surplus
            "Rent: Surplus (vs buying house)": rent_monthly_surpluses,
        }
        rows = []
        date = self.start_date
        for _ in range(self.num_months + 1):
            rows.append(date.strftime("%b %d, %Y"))
            date = math_utils.increment_month(date)
        return to_df(cols, rows, multi_col=True)
