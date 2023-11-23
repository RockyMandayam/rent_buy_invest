from dataclasses import dataclass
from typing import Any, List, Optional

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df


@dataclass
class InitialState:
    rent_one_time_cost: float
    house_one_time_cost: float
    invested_in_market_if_renting: float
    invested_in_house: float

    def __init__(self, house_config: HouseConfig, rent_config: RentConfig) -> None:
        self.rent_one_time_cost = rent_config.get_upfront_one_time_cost()
        self.house_one_time_cost = house_config.get_upfront_one_time_cost()
        assert (
            self.rent_one_time_cost < self.house_one_time_cost
        ), "Renting should have a smaller upfront one-time cost than buying a house."
        self.invested_in_house = house_config.get_down_payment()
        self.invested_in_market_if_renting = (
            self.house_one_time_cost + self.invested_in_house - self.rent_one_time_cost
        )

    def get_df(self) -> List[List[Optional[Any]]]:
        rows = ["One-time costs", "Invested in market", "Invested in house"]
        cols = {
            "Rent": [self.rent_one_time_cost, self.invested_in_market_if_renting, 0],
            "House": [self.house_one_time_cost, 0, self.invested_in_house],
        }
        return to_df(cols, rows)
