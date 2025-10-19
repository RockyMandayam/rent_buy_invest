from dataclasses import dataclass
from typing import Any

from rent_buy_invest.utils.data_utils import to_df


@dataclass(frozen=True)
class FinalState:
    wealth_if_renting: float
    wealth_if_buying: float

    def get_df(self) -> list[list[Any | None]]:
        rows = ["Wealth"]
        cols = {
            "Rent": [self.wealth_if_renting],
            "Buy": [self.wealth_if_buying],
        }
        return to_df(cols, rows)
