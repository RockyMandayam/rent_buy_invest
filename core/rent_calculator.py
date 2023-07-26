from typing import List, Tuple

from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.core.rent_config import RentConfig


class RentCalculator:
    def __init__(
        self,
        rent_config: RentConfig,
        market_config: MarketConfig,
        num_months: int,
        initial_state: InitialState,
    ):
        self.rent_config = rent_config
        self.market_config = market_config
        self.num_months = num_months
        self.initial_state = initial_state

    def calculate(self) -> Tuple[Tuple[str, List[float]]]:
        rent_monthly_costs = self.rent_config.get_monthly_costs_of_renting(
            self.num_months
        )
        rent_investment_monthly = self.market_config.get_pretax_monthly_wealth(
            self.initial_state.rent_invested, self.num_months
        )
        return ("Monthly costs", rent_monthly_costs), (
            "Investment",
            rent_investment_monthly,
        )
