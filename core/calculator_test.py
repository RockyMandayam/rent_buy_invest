import pytest

# isort: off
from rent_buy_invest.core.calculator import (
    PMI_LTV_THRESHOLD,
    Calculator,
)

# isort: on
from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.experiment_config_test import TestExperimentConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

EXPERIMENT_CONFIG = ExperimentConfig.parse(TestExperimentConfig.TEST_CONFIG_PATH)


class TestCalculator:
    def test_calculate(self) -> None:
        calculator = Calculator(
            EXPERIMENT_CONFIG.buy_config,
            EXPERIMENT_CONFIG.rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.personal_config,
            EXPERIMENT_CONFIG.num_months,
            EXPERIMENT_CONFIG.start_date,
            InitialState.from_configs(
                EXPERIMENT_CONFIG.buy_config, EXPERIMENT_CONFIG.rent_config
            ),
        )

        # initial state tested separately
        projection = calculator.calculate()

        first_row = projection.iloc[0, :]
        first_month_home_value_related_cost_fraction = (
            first_row["Buy"]["Costs Tied to Home Value"]
            / first_row["Buy"]["Home Value"]
        )
        first_month_monthly_mortgage_total_payment = first_row["Buy"][
            "Mortgage Payment"
        ]

        for row_index in range(projection.shape[0]):
            row = projection.iloc[row_index, :]

            first_row_of_year = projection.iloc[
                (row_index // MONTHS_PER_YEAR) * MONTHS_PER_YEAR, :
            ]
            assert row["Buy"]["Costs Tied to Home Value"] / first_row_of_year["Buy"][
                "Home Value"
            ] == pytest.approx(first_month_home_value_related_cost_fraction, rel=0.0001)

            monthly_mortgage_total_payment = row["Buy"]["Mortgage Payment"]
            assert (
                row["Buy"]["Mortgage Interest Payment"]
                + row["Buy"]["Mortgage Equity Payment"]
                == monthly_mortgage_total_payment
            )
            assert (
                monthly_mortgage_total_payment
                == pytest.approx(first_month_monthly_mortgage_total_payment, abs=0.01)
                # if it is off by 0.5 cents every payment due to rounding...
                or monthly_mortgage_total_payment
                <= EXPERIMENT_CONFIG.num_months * 0.005
            )

            loan_amount = row["Buy"]["Loan Amount"]
            mortgage_insurance = row["Buy"]["Mortgage Insurance"]
            if (
                loan_amount
                <= PMI_LTV_THRESHOLD * EXPERIMENT_CONFIG.buy_config.sale_price
            ):
                assert mortgage_insurance == 0
            else:
                assert mortgage_insurance == round(
                    EXPERIMENT_CONFIG.buy_config.annual_mortgage_insurance_fraction
                    * loan_amount,
                    2,
                )

            home_monthly_cost = (
                row["Buy"]["Costs Tied to Home Value"]
                + row["Buy"]["Costs Tied to Inflation"]
                + monthly_mortgage_total_payment
                + mortgage_insurance
            )
            rent_monthly_cost = row["Rent"]["Costs Tied to Inflation"]
            # TODO improve this whole test and more easily test this, including with FHA loans and for PMI being removed with a home appraisal
            # if home_monthly_cost >= rent_monthly_cost:
            #     assert row["Buy"]["Surplus (vs renting)"] == 0
            #     assert row["Rent"]["Surplus (vs buying home)"] == pytest.approx(
            #         home_monthly_cost - rent_monthly_cost, abs=0.0001
            #     )
            # else:
            #     assert row["Rent"]["Surplus (vs buying home)"] == 0
            #     assert row["Buy"]["Surplus (vs renting)"] == pytest.approx(
            #         rent_monthly_cost - home_monthly_cost, abs=0.0001
            #     )
