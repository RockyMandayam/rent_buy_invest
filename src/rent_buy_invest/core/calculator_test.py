import pytest

from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.experiment_config_test import TestExperimentConfig
from rent_buy_invest.core.calculator import Calculator
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.mortgage_insurance import PMI_LTV_THRESHOLD
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

EXPERIMENT_CONFIG = ExperimentConfig.parse(TestExperimentConfig.TEST_CONFIG_PATH)
PRIMARY_RESIDENCE_EXPERIMENT_CONFIG = ExperimentConfig.parse(
    "rent_buy_invest/core/test_resources/test-primary-residence-experiment-config.yaml"
)


class TestCalculator:
    def test_calculate(self) -> None:
        calculator = Calculator(
            EXPERIMENT_CONFIG.buy_config,
            EXPERIMENT_CONFIG.rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.personal_config,
            EXPERIMENT_CONFIG.num_years,
            EXPERIMENT_CONFIG.start_date,
            InitialState.from_configs(
                EXPERIMENT_CONFIG.buy_config,
                EXPERIMENT_CONFIG.rent_config,
                EXPERIMENT_CONFIG.market_config,
                EXPERIMENT_CONFIG.personal_config,
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
                <= EXPERIMENT_CONFIG.num_years * MONTHS_PER_YEAR * 0.005
            )

            loan_amount = row["Buy"]["Loan Amount"]
            mortgage_insurance = row["Buy"]["Mortgage Insurance"]
            if (
                loan_amount
                <= PMI_LTV_THRESHOLD * EXPERIMENT_CONFIG.buy_config.purchase_price
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

    def test_calculate_applies_the_mortgage_interest_deduction(self) -> None:
        """The deduction has to reach the cash flow, not just the output column.

        It was computed and published as ``Mortgage Interest Deduction Savings``
        for a long time without ever being subtracted from what buying costs,
        which left it with no effect on the answer at all. The whole suite passed
        the entire time, so this pins the subtraction rather than the column.

        The two worlds' net monthly costs are not published, but their difference
        is: exactly one of the two surpluses is non-zero each month, and the pair
        is the gap between the two costs.
        """
        calculator = Calculator(
            EXPERIMENT_CONFIG.buy_config,
            EXPERIMENT_CONFIG.rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.personal_config,
            EXPERIMENT_CONFIG.num_years,
            EXPERIMENT_CONFIG.start_date,
            InitialState.from_configs(
                EXPERIMENT_CONFIG.buy_config,
                EXPERIMENT_CONFIG.rent_config,
                EXPERIMENT_CONFIG.market_config,
                EXPERIMENT_CONFIG.personal_config,
            ),
        )
        projection = calculator.calculate()

        deduction_savings = projection["Buy"]["Mortgage Interest Deduction Savings"]
        # a config that never deducts anything would pass this test vacuously
        assert (deduction_savings > 0).any()

        for row_index in range(projection.shape[0]):
            row = projection.iloc[row_index, :]
            buy_net_monthly_cost = (
                row["Buy"]["Costs Tied to Home Value"]
                + row["Buy"]["Costs Tied to Inflation"]
                + row["Buy"]["Mortgage Payment"]
                + row["Buy"]["Mortgage Insurance"]
                + row["Buy"]["One-Off Costs"]
                + row["Buy"]["Tax on Rental Income"]
                - row["Buy"]["Rental Income (Pre-Tax)"]
                - row["Buy"]["Mortgage Interest Deduction Savings"]
            )
            rent_net_monthly_cost = row["Rent"]["Costs Tied to Inflation"]
            gap_between_the_two_worlds = row["Rent"]["Surplus"] - row["Buy"]["Surplus"]
            assert gap_between_the_two_worlds == pytest.approx(
                buy_net_monthly_cost - rent_net_monthly_cost, abs=0.01
            )

    def test_calculate_for_primary_residence(self) -> None:
        """A home lived in rather than rented out projects over the full horizon.

        No other config in this repo leaves rental_income_config null, so without
        this the whole primary-residence path goes unexercised.
        """
        experiment_config = PRIMARY_RESIDENCE_EXPERIMENT_CONFIG
        assert experiment_config.buy_config.rental_income_config is None

        calculator = Calculator(
            experiment_config.buy_config,
            experiment_config.rent_config,
            experiment_config.market_config,
            experiment_config.personal_config,
            experiment_config.num_years,
            experiment_config.start_date,
            InitialState.from_configs(
                experiment_config.buy_config,
                experiment_config.rent_config,
                experiment_config.market_config,
                experiment_config.personal_config,
            ),
        )
        projection = calculator.calculate()

        assert projection.shape[0] == experiment_config.num_years * MONTHS_PER_YEAR + 1
        assert (projection["Buy"]["Rental Income (Pre-Tax)"] == 0).all()
        assert (projection["Buy"]["Tax on Rental Income"] == 0).all()
