import copy

import pytest

from rent_buy_invest.configs.buy_config_test import TestBuyConfig
from rent_buy_invest.configs.rent_config_test import TestRentConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.utils.data_utils import to_df


class TestInitialState:
    def test_get_df(self) -> None:
        initial_state = InitialState.from_configs(
            TestBuyConfig.BUY_CONFIG, TestRentConfig.RENT_CONFIG
        )
        act = initial_state.get_df()

        # total money put in initially must be same in both cases
        assert (
            act.loc["Upfront one-time costs", "Rent"]
            + act.loc["Invested (Pre-Tax)", "Rent"]
            + act.loc["Home equity", "Rent"]
            == act.loc["Upfront one-time costs", "Buy"]
            + act.loc["Invested (Pre-Tax)", "Buy"]
            + act.loc["Home equity", "Buy"]
        )

        # now for a more specific test
        exp_rows = ["Upfront one-time costs", "Home equity", "Invested (Pre-Tax)"]
        exp_cols = {
            "Rent": [
                TestRentConfig.RENT_CONFIG.get_upfront_one_time_cost(),
                0,
                TestBuyConfig.BUY_CONFIG.get_upfront_one_time_cost()
                + TestBuyConfig.BUY_CONFIG.down_payment
                - TestRentConfig.RENT_CONFIG.get_upfront_one_time_cost(),
            ],
            "Buy": [
                TestBuyConfig.BUY_CONFIG.get_upfront_one_time_cost(),
                TestBuyConfig.BUY_CONFIG.down_payment,
                0,
            ],
        }
        exp = to_df(exp_cols, exp_rows)
        assert act.equals(exp)

        rent_config_bad = copy.deepcopy(TestRentConfig.RENT_CONFIG)
        rent_config_bad.security_deposit = 1000000
        with pytest.raises(AssertionError):
            initial_state = InitialState.from_configs(
                TestBuyConfig.BUY_CONFIG, rent_config_bad
            )
