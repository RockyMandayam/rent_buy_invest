import pytest

from rent_buy_invest.core.calculator import (
    MAXIMUM_MORTGAGE_AMOUNT_FRACTION_WITH_NO_PMI,
    Calculator,
)
from rent_buy_invest.core.experiment_config_test import EXPERIMENT_CONFIG
from rent_buy_invest.core.initial_state import InitialState


class TestCalculator:
    def test_calculate(self) -> None:
        calculator = Calculator(
            EXPERIMENT_CONFIG.house_config,
            EXPERIMENT_CONFIG.rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.num_months,
            EXPERIMENT_CONFIG.start_date,
            InitialState(EXPERIMENT_CONFIG.house_config, EXPERIMENT_CONFIG.rent_config),
        )

        # initial state tested separately

        # TODO do an exact comparison of the project vs my by-hand calculations.
        projection = calculator.calculate()

        first_row = projection.iloc[0, :]
        first_month_house_value_related_cost_fraction = (
            first_row["House"]["House: Monthly cost tied to house value"]
            / first_row["House"]["House: House value"]
        )
        first_month_monthly_mortgage_total_payment = first_row["House"][
            "House: Monthly mortgage total payment"
        ]

        for row_index in range(projection.shape[0]):
            row = projection.iloc[row_index, :]

            assert row["House"]["House: Monthly cost tied to house value"] / row[
                "House"
            ]["House: House value"] == pytest.approx(
                first_month_house_value_related_cost_fraction, rel=0.0001
            )

            monthly_mortgage_total_payment = row["House"][
                "House: Monthly mortgage total payment"
            ]
            assert (
                row["House"]["House: Monthly mortgage interest payment"]
                + row["House"]["House: Monthly mortgage equity payment"]
                == monthly_mortgage_total_payment
            )
            assert (
                monthly_mortgage_total_payment
                == pytest.approx(first_month_monthly_mortgage_total_payment, abs=0.01)
                # if it is off by 0.5 cents every payment due to rounding...
                or monthly_mortgage_total_payment
                <= EXPERIMENT_CONFIG.num_months * 0.005
            )

            mortgage_amount = row["House"]["House: Mortgage amount"]
            pmi = row["House"]["House: Monthly cost of PMI"]
            if (
                mortgage_amount
                <= MAXIMUM_MORTGAGE_AMOUNT_FRACTION_WITH_NO_PMI
                * EXPERIMENT_CONFIG.house_config.sale_price
            ):
                assert pmi == 0
            else:
                assert pmi == round(
                    EXPERIMENT_CONFIG.house_config.pmi_fraction * mortgage_amount, 2
                )

            house_monthly_cost = (
                row["House"]["House: Monthly cost tied to house value"]
                + row["House"]["House: Monthly cost tied to inflation"]
                + monthly_mortgage_total_payment
                + pmi
            )
            rent_monthly_cost = row["Rent"]["Rent: Monthly cost tied to inflation"]
            if house_monthly_cost >= rent_monthly_cost:
                assert row["House"]["House: Monthly surplus (relative to renting)"] == 0
                assert row["Rent"][
                    "Rent: Monthly surplus (relative to buying a house)"
                ] == pytest.approx(house_monthly_cost - rent_monthly_cost, abs=0.0001)
            else:
                assert (
                    row["Rent"]["Rent: Monthly surplus (relative to buying a house)"]
                    == 0
                )
                assert row["House"][
                    "House: Monthly surplus (relative to renting)"
                ] == pytest.approx(rent_monthly_cost - house_monthly_cost, abs=0.0001)
