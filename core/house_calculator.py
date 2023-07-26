from typing import List, Tuple

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.rent_config import RentConfig


class HouseCalculator:
    """ Calculates projection of financial state when owning a house. """
    def __init__(
        self,
        house_config: HouseConfig,
        rent_config: RentConfig,
        num_months: int,
        initial_state: InitialState,
    ):
        self.house_config: HouseConfig = house_config
        self.rent_config: RentConfig = rent_config
        self.num_months: int = num_months
        self.initial_state: InitialState = initial_state

    def calculate(self) -> Tuple[Tuple[str, List[float]]]:
        """Calculates projection of financial state when owning a house.

        Returns:
            # TODO document this. Mention how it returns a nested tuple instead of a dict due to order
        """
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
        # will build these ones in the loop
        mortgage_interests = []
        paid_toward_equity = []
        equities = []
        pmis = []

        mortgage_amount = self.house_config.get_initial_mortgage_amount()
        monthly_mortgage_payment = self.house_config.get_monthly_mortgage_payment()
        for month in range(self.num_months):
            mortgage_interest = (
                mortgage_amount * self.house_config.mortgage_annual_interest_rate / 12
            )
            mortgage_interests.append(round(mortgage_interest, 2))
            toward_equity = monthly_mortgage_payment - mortgage_interest
            paid_toward_equity.append(round(toward_equity, 2))
            equities.append(round(house_values[month] - mortgage_amount, 2))
            pmis.append(self.house_config.pmi_fraction * mortgage_amount)
            mortgage_amount -= toward_equity
            assert mortgage_annual_interest_rate >= 0, "Mortgage amount cannot be negative."
        return (
            (
                "House value related monthly cost",
                house_monthly_costs_related_to_house_value,
            ),
            ("House value", house_values),
            (
                "Inflation related monthly cost",
                house_monthly_costs_related_to_inflation,
            ),
            ("Mortgage interest", mortgage_interests),
            ("Paid toward equity", paid_toward_equity),
            ("Total mortgage payment", [monthly_mortgage_payment] * self.num_months),
            ("PMI", pmis),
            ("Equity", equities),
        )
