from dataclasses import dataclass
from typing import Any

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df


@dataclass(frozen=True)
class InitialState:
    rent_one_time_cost: float
    house_one_time_cost: float
    invested_in_market_if_renting: float
    invested_in_house: float

    @staticmethod
    def from_configs(house_config: HouseConfig, rent_config: RentConfig) -> None:
        rent_one_time_cost = rent_config.get_upfront_one_time_cost()
        house_one_time_cost = house_config.get_upfront_one_time_cost()
        assert (
            rent_one_time_cost <= house_one_time_cost
        ), "Renting should not have a larger upfront one-time cost than buying a house."
        invested_in_house = house_config.get_down_payment()
        invested_in_market_if_renting = (
            house_one_time_cost + invested_in_house - rent_one_time_cost
        )
        return InitialState(
            rent_one_time_cost,
            house_one_time_cost,
            invested_in_market_if_renting,
            invested_in_house,
        )

    def get_df(self) -> list[list[Any | None]]:
        rows = ["One-time costs", "Invested in market", "Invested in house"]
        cols = {
            "Rent": [self.rent_one_time_cost, self.invested_in_market_if_renting, 0],
            "House": [self.house_one_time_cost, 0, self.invested_in_house],
        }
        return to_df(cols, rows)
