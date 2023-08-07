from dataclasses import dataclass
from typing import Any, List, Optional

import pandas as pd

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.utils.data_utils import to_df


@dataclass
class InitialState:
    # TODO test this class
    rent_one_time_cost: float
    house_one_time_cost: float
    rent_invested: float
    house_invested: float

    def __init__(self, house_config: HouseConfig) -> None:
        # TODO what if rent_one_time_cost is non-zero? Can this be negative? Make this a parameter?
        self.rent_one_time_cost = 0
        self.house_one_time_cost = house_config.get_upfront_one_time_cost()
        assert (
            self.rent_one_time_cost < self.house_one_time_cost
        ), "Renting should have a smaller upfront one-time cost than buying a house."
        self.house_invested = house_config.get_down_payment()
        self.rent_invested = (
            self.house_one_time_cost + self.house_invested - self.rent_one_time_cost
        )

    def get_df(self) -> List[List[Optional[Any]]]:
        cols = {
            "Rent": [self.rent_one_time_cost, self.rent_invested],
            "House": [self.house_one_time_cost, self.house_invested],
        }
        rows = ["One-time costs", "Invested (in market or house)"]
        return to_df(cols, rows)
