from dataclasses import dataclass
from typing import Any

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.configs.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df


@dataclass(frozen=True)
class InitialState:
    rent_upfront_one_time_cost: float
    buy_upfront_one_time_cost: float
    invested_if_renting: float
    home_equity_if_buying: float

    @staticmethod
    def from_configs(
        buy_config: BuyConfig,
        rent_config: RentConfig,
        market_config: MarketConfig,
        personal_config: PersonalConfig,
    ) -> "InitialState":
        # upfront costs are unrecoverable ("out the door") costs (e.g., not invested, don't grow, etc.)
        rent_upfront_one_time_cost = rent_config.get_upfront_one_time_cost()
        buy_upfront_one_time_cost = buy_config.get_upfront_one_time_cost()

        # account for savings due to mortgage discount points income tax deduction
        discount_points_fee = (
            buy_config.mortgage_discount_points_fee_fraction
            * buy_config.initial_loan_amount
        )
        discount_points_deduction_savings = (
            market_config.get_income_tax_savings_from_deduction(
                personal_config.ordinary_income, discount_points_fee
            )
        )
        buy_upfront_one_time_cost -= discount_points_deduction_savings

        # just a kind of sanity check, the upfront cost for buying should basically always be more than for renting
        assert (
            rent_upfront_one_time_cost <= buy_upfront_one_time_cost
        ), f"The upfront one-time cost for renting (${rent_upfront_one_time_cost}) must not be larger than for buying (${buy_upfront_one_time_cost})."

        # calculate invested amounts for rent vs buy
        # for rent, the "surplus" amount that would have otherwise been an upfront cost for buying instead is invested
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
        rows = ["Upfront one-time costs", "Home equity", "Invested (Pre-Tax)"]
        cols = {
            "Rent": [self.rent_upfront_one_time_cost, 0, self.invested_if_renting],
            "Buy": [self.buy_upfront_one_time_cost, self.home_equity_if_buying, 0],
        }
        return to_df(cols, rows)
