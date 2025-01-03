import copy

import pytest

from rent_buy_invest.configs.buy_config_test import BUY_CONFIG
from rent_buy_invest.configs.rent_config_test import RENT_CONFIG
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.utils.data_utils import to_df


class TestInitialState:
    def test_get_df(self) -> None:
        initial_state = InitialState.from_configs(BUY_CONFIG, RENT_CONFIG)
        act = initial_state.get_df()

        # total money put in initially must be same in both cases
        assert (
            act.loc["Upfront one-time costs", "Rent"]
            + act.loc["Invested", "Rent"]
            + act.loc["Home equity", "Rent"]
            == act.loc["Upfront one-time costs", "Buy"]
            + act.loc["Invested", "Buy"]
            + act.loc["Home equity", "Buy"]
        )

        # now for a more specific test
        exp_rows = ["Upfront one-time costs", "Home equity", "Invested"]
        exp_cols = {
            "Rent": [
                RENT_CONFIG.get_upfront_one_time_cost(),
                0,
                BUY_CONFIG.get_upfront_one_time_cost()
                + BUY_CONFIG.down_payment
                - RENT_CONFIG.get_upfront_one_time_cost(),
            ],
            "Buy": [
                BUY_CONFIG.get_upfront_one_time_cost(),
                BUY_CONFIG.down_payment,
                0,
            ],
        }
        exp = to_df(exp_cols, exp_rows)
        assert act.equals(exp)

        rent_config_bad = copy.deepcopy(RENT_CONFIG)
        rent_config_bad.security_deposit = 1000000
        with pytest.raises(AssertionError):
            initial_state = InitialState.from_configs(BUY_CONFIG, rent_config_bad)
