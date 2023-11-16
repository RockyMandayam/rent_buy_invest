from dataclasses import dataclass
from typing import Any, List, Optional

import pandas as pd

# from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.house_config_test import HOUSE_CONFIG
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.rent_config_test import RENT_CONFIG
from rent_buy_invest.utils.data_utils import to_df


class TestInitialState:
    def test_get_df(self) -> None:
        initial_state = InitialState(HOUSE_CONFIG, RENT_CONFIG)
        act = initial_state.get_df()

        exp_rows = ["One-time costs", "Invested (in market or house)"]
        exp_cols = {
            "Rent": [
                RENT_CONFIG.get_upfront_one_time_cost(),
                HOUSE_CONFIG.get_upfront_one_time_cost()
                + HOUSE_CONFIG.get_down_payment()
                - RENT_CONFIG.get_upfront_one_time_cost(),
            ],
            "House": [
                HOUSE_CONFIG.get_upfront_one_time_cost(),
                HOUSE_CONFIG.get_down_payment(),
            ],
        }
        exp = to_df(exp_cols, exp_rows)
        assert act.equals(exp)
