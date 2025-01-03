import pytest

# isort: off
from rent_buy_invest.core.calculator import (
    PMI_LTV_THRESHOLD,
    Calculator,
)

# isort: on
from rent_buy_invest.core.experiment_config_test import EXPERIMENT_CONFIG
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


class TestCalculator:
    def test_calculate(self) -> None:
        calculator = Calculator(
            EXPERIMENT_CONFIG.house_config,
            EXPERIMENT_CONFIG.rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.num_months,
            EXPERIMENT_CONFIG.start_date,
            InitialState.from_configs(
                EXPERIMENT_CONFIG.house_config, EXPERIMENT_CONFIG.rent_config
            ),
        )

        # initial state tested separately
        projection = calculator.calculate()

        first_row = projection.iloc[0, :]
        first_month_home_value_related_cost_fraction = (
            first_row["Buy"]["Cost tied to market value"]
            / first_row["Buy"]["Market value"]
        )
        first_month_monthly_mortgage_total_payment = first_row["Buy"][
            "Mortgage payment"
        ]

        for row_index in range(projection.shape[0]):
            row = projection.iloc[row_index, :]

            first_row_of_year = projection.iloc[
                (row_index // MONTHS_PER_YEAR) * MONTHS_PER_YEAR, :
            ]
            assert row["Buy"]["Cost tied to market value"] / first_row_of_year["Buy"][
                "Market value"
            ] == pytest.approx(first_month_home_value_related_cost_fraction, rel=0.0001)

            monthly_mortgage_total_payment = row["Buy"]["Mortgage payment"]
            assert (
                row["Buy"]["Mortgage interest payment"]
                + row["Buy"]["Mortgage equity payment"]
                == monthly_mortgage_total_payment
            )
            assert (
                monthly_mortgage_total_payment
                == pytest.approx(first_month_monthly_mortgage_total_payment, abs=0.01)
                # if it is off by 0.5 cents every payment due to rounding...
                or monthly_mortgage_total_payment
                <= EXPERIMENT_CONFIG.num_months * 0.005
            )

            loan_amount = row["Buy"]["Loan amount"]
            mortgage_insurance = row["Buy"]["Mortgage Insurance"]
            if (
                loan_amount
                <= PMI_LTV_THRESHOLD * EXPERIMENT_CONFIG.house_config.sale_price
            ):
                assert mortgage_insurance == 0
            else:
                assert mortgage_insurance == round(
                    EXPERIMENT_CONFIG.house_config.annual_mortgage_insurance_fraction
                    * loan_amount,
                    2,
                )

            home_monthly_cost = (
                row["Buy"]["Cost tied to market value"]
                + row["Buy"]["Cost tied to inflation"]
                + monthly_mortgage_total_payment
                + mortgage_insurance
            )
            rent_monthly_cost = row["Rent"]["Cost tied to inflation"]
            # TODO improve this whole test and more easily test this, including with FHA loans and for PMI being removed with a home appraisal
            # if home_monthly_cost >= rent_monthly_cost:
            #     assert row["Buy"]["Surplus (vs renting)"] == 0
            #     assert row["Rent"]["Surplus (vs buying house)"] == pytest.approx(
            #         home_monthly_cost - rent_monthly_cost, abs=0.0001
            #     )
            # else:
            #     assert row["Rent"]["Surplus (vs buying house)"] == 0
            #     assert row["Buy"]["Surplus (vs renting)"] == pytest.approx(
            #         rent_monthly_cost - home_monthly_cost, abs=0.0001
            #     )
