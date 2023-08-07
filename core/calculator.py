from typing import List, Tuple

import pandas as pd

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df


class Calculator:
    def __init__(
        self,
        house_config: HouseConfig,
        rent_config: RentConfig,
        market_config: MarketConfig,
        num_months: int,
        initial_state: InitialState,
    ):
        self.house_config: HouseConfig = house_config
        self.rent_config: RentConfig = rent_config
        self.market_config: MarketConfig = market_config
        self.num_months: int = num_months
        self.initial_state: InitialState = initial_state

    def calculate(self) -> pd.DataFrame:
        # Some housing costs/gains can be calculated independently at once
        house_values = self.house_config.get_monthly_house_values(self.num_months)
        house_monthly_costs_related_to_house_value = (
            self.house_config.get_house_value_related_monthly_costs(self.num_months)
        )
        house_monthly_costs_related_to_inflation = (
            # TODO don't use rent inflation maybe? Use something else for utilities for rent and house?
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
        equities = [self.house_config.get_down_payment()]
        pmis = []
        # # TODO monthly surplus
        # monthly_surplus_housing = []
        # monthly_surplus_rent = []
        rent_investment_monthly = self.market_config.get_pretax_monthly_wealth(
            self.initial_state.rent_invested, self.num_months
        )

        mortgage_amount = self.house_config.get_initial_mortgage_amount()
        monthly_mortgage_payment = self.house_config.get_monthly_mortgage_payment()
        for month in range(self.num_months):
            mortgage_interest = (
                mortgage_amount * self.house_config.mortgage_annual_interest_rate / 12
            )
            mortgage_interests.append(round(mortgage_interest, 2))
            toward_equity = round(monthly_mortgage_payment - mortgage_interest, 2)
            paid_toward_equity.append(toward_equity)
            equities.append(round(house_values[month] - mortgage_amount, 2))
            pmis.append(self.house_config.pmi_fraction * mortgage_amount)
            mortgage_amount -= toward_equity
            assert mortgage_amount >= 0, "Mortgage amount cannot be negative."
        # TODO fix this - for now removing last element to make all cols have same num of rows
        equities.pop()

        # RELIES on the fact that python dictionaries are now ordered
        cols = {
            "House: House value related monthly cost": house_monthly_costs_related_to_house_value,
            "House: House value": house_values,
            "House: Inflation related monthly cost": house_monthly_costs_related_to_inflation,
            "House: Mortgage interest": mortgage_interests,
            "House: Paid toward equity": paid_toward_equity,
            # black formats the following line in a easy-to-misread way
            # fmt: off
            "House: Total mortgage payment": [monthly_mortgage_payment] * self.num_months,
            # fmt: on
            "House: PMI": pmis,
            "House: Equity": equities,
            "Rent: Monthly cost": rent_monthly_costs,
            "Rent: Investment": rent_investment_monthly,
        }
        return to_df(cols)
