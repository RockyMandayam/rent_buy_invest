from dataclasses import dataclass
from typing import Any

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df


@dataclass(frozen=True)
class InitialState:
    rent_upfront_one_time_cost: float
    buy_upfront_one_time_cost: float
    invested_if_renting: float
    home_equity_if_buying: float

    @staticmethod
    def from_configs(buy_config: BuyConfig, rent_config: RentConfig) -> None:
        rent_upfront_one_time_cost = rent_config.get_upfront_one_time_cost()
        buy_upfront_one_time_cost = buy_config.get_upfront_one_time_cost()
        assert (
            rent_upfront_one_time_cost <= buy_upfront_one_time_cost
        ), "Renting should not have a larger upfront one-time cost than buying a home."
        home_equity_if_buying = buy_config.down_payment
        invested_if_renting = (
            buy_upfront_one_time_cost
            + home_equity_if_buying
            - rent_upfront_one_time_cost
        )
        return InitialState(
            rent_upfront_one_time_cost,
            buy_upfront_one_time_cost,
            invested_if_renting,
            home_equity_if_buying,
        )

    def get_df(self) -> list[list[Any | None]]:
        rows = ["Upfront one-time costs", "Home equity", "Invested"]
        cols = {
            "Rent": [self.rent_upfront_one_time_cost, 0, self.invested_if_renting],
            "Buy": [self.buy_upfront_one_time_cost, self.home_equity_if_buying, 0],
        }
        return to_df(cols, rows)
