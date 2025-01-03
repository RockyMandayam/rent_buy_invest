from dataclasses import dataclass
from typing import Any

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df


@dataclass(frozen=True)
class InitialState:
    rent_one_time_cost: float
    home_one_time_cost: float
    invested_in_market_if_renting: float
    invested_in_home: float

    @staticmethod
    def from_configs(buy_config: BuyConfig, rent_config: RentConfig) -> None:
        rent_one_time_cost = rent_config.get_upfront_one_time_cost()
        home_one_time_cost = buy_config.get_upfront_one_time_cost()
        assert (
            rent_one_time_cost <= home_one_time_cost
        ), "Renting should not have a larger upfront one-time cost than buying a house."
        invested_in_home = buy_config.down_payment
        invested_in_market_if_renting = (
            home_one_time_cost + invested_in_home - rent_one_time_cost
        )
        return InitialState(
            rent_one_time_cost,
            home_one_time_cost,
            invested_in_market_if_renting,
            invested_in_home,
        )

    def get_df(self) -> list[list[Any | None]]:
        rows = ["One-time costs", "Invested in market", "Invested in house"]
        cols = {
            "Rent": [self.rent_one_time_cost, self.invested_in_market_if_renting, 0],
            "Buy": [self.home_one_time_cost, 0, self.invested_in_home],
        }
        return to_df(cols, rows)
