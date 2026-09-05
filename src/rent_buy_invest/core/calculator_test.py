from copy import deepcopy

import pytest

from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.experiment_config_test import TestExperimentConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.calculator import (
    MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE,
    Calculator,
)
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.mortgage_insurance import PMI_LTV_THRESHOLD
from rent_buy_invest.core.tax import TaxableAmounts, TaxModule
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR, avg

EXPERIMENT_CONFIG = ExperimentConfig.parse(TestExperimentConfig.TEST_CONFIG_PATH)
PRIMARY_RESIDENCE_EXPERIMENT_CONFIG = ExperimentConfig.parse(
    "rent_buy_invest/core/test_resources/test-primary-residence-experiment-config.yaml"
)


def _deductible_mortgage_interest_for_the_year(projection, month: int) -> float:
    """The interest deductible in the tax year ending at ``month``, in dollars."""
    first_month_of_year = month + 1 - MONTHS_PER_YEAR
    interest_for_the_year = projection["Buy"]["Mortgage Interest Payment"][
        first_month_of_year : month + 1
    ].sum()
    avg_loan_amount = avg(
        list(projection["Buy"]["Loan Amount"][first_month_of_year : month + 1])
    )
    deductible_fraction = MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE / max(
        MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE, avg_loan_amount
    )
    return deductible_fraction * interest_for_the_year


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
                + row["Buy"]["Management Fee"]
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

    def test_calculate_prorates_the_deduction_not_the_saving_on_a_jumbo_loan(
        self,
    ) -> None:
        """Over the balance cap, the deduction shrinks -- not the tax saving.

        Scaling the saving instead prices the surviving interest at the average
        rate of the whole deduction, including the lower brackets the real,
        smaller deduction never reaches. Every example config in this repo has a
        loan under the cap, where the two agree exactly, so the prorating path
        goes unexercised without a deliberately oversized loan here.
        """
        experiment_config = deepcopy(EXPERIMENT_CONFIG)
        # four times the price, so the loan clears the cap with room to spare
        experiment_config.buy_config.purchase_price *= 4
        assert (
            experiment_config.buy_config.initial_loan_amount
            > MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE
        )

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

        num_months = experiment_config.num_years * MONTHS_PER_YEAR
        ordinary_incomes = experiment_config.personal_config.get_ordinary_incomes(
            num_months
        )
        market_config = experiment_config.market_config
        tax_module = TaxModule(market_config)
        years_where_the_two_formulas_disagree = 0

        for month in range(MONTHS_PER_YEAR - 1, num_months + 1, MONTHS_PER_YEAR):
            first_month_of_year = month + 1 - MONTHS_PER_YEAR
            interest_for_the_year = projection["Buy"]["Mortgage Interest Payment"][
                first_month_of_year : month + 1
            ].sum()
            avg_loan_amount = avg(
                list(projection["Buy"]["Loan Amount"][first_month_of_year : month + 1])
            )
            annual_income = sum(ordinary_incomes[first_month_of_year : month + 1])
            deductible_fraction = (
                MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE
                / max(
                    MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE,
                    avg_loan_amount,
                )
            )
            salary = TaxableAmounts(ordinary_income=annual_income)
            prorated_deduction = -tax_module.extra_tax_from(
                month,
                salary,
                TaxableAmounts(
                    ordinary_deductions=deductible_fraction * interest_for_the_year
                ),
            ).ordinary
            prorated_saving = (
                deductible_fraction
                * -tax_module.extra_tax_from(
                    month,
                    salary,
                    TaxableAmounts(ordinary_deductions=interest_for_the_year),
                ).ordinary
            )

            reported = projection["Buy"]["Mortgage Interest Deduction Savings"].iloc[
                month
            ]
            assert reported == pytest.approx(prorated_deduction, abs=0.01)
            if prorated_deduction != pytest.approx(prorated_saving, abs=0.01):
                years_where_the_two_formulas_disagree += 1
                # a deduction comes off the top of income first, so prorating the
                # saving can only ever come out low
                assert prorated_saving < prorated_deduction

        # without this the assertions above would hold for either formula
        assert years_where_the_two_formulas_disagree > 0

    def test_calculate_stacks_the_years_two_ordinary_income_adjustments(
        self,
    ) -> None:
        """Rent received and the mortgage interest deduction land on each other.

        Rent raises taxable income and the deduction lowers it, so whichever is
        charged second lands in the bracket the first one moved you to. Working
        each out from salary alone -- which this did until now -- prices some of
        each in a bracket the year never reaches. Only their combined effect is a
        fact; the split between the two reported columns is a convention (all
        income first, then deductions off the top), so this checks the total.
        """
        # The shared config's brackets are flat across the whole range this
        # scenario touches, so stacking could never change a number in it. These
        # put a boundary right where the year's salary sits, which is what a real
        # federal schedule does.
        experiment_config = deepcopy(EXPERIMENT_CONFIG)
        assert experiment_config.buy_config.rental_income_config is not None
        experiment_config.market_config = MarketConfig(
            market_rate_of_return=experiment_config.market_config.market_rate_of_return,
            market_dividend_yield=0.0,
            tax_brackets_inflation=0.0,
            annual_inflation_rate=experiment_config.market_config.annual_inflation_rate,
            tax_brackets={
                "ordinary_income_tax_brackets": [
                    {"upper_limit": 105_000.0, "tax_rate": 0.10},
                    {"upper_limit": float("inf"), "tax_rate": 0.37},
                ],
                "long_term_capital_gains_tax_brackets": [
                    {"upper_limit": 105_000.0, "tax_rate": 0.0},
                    {"upper_limit": float("inf"), "tax_rate": 0.20},
                ],
            },
        )
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

        market_config = experiment_config.market_config
        num_months = experiment_config.num_years * MONTHS_PER_YEAR
        ordinary_incomes = experiment_config.personal_config.get_ordinary_incomes(
            num_months
        )
        years_where_stacking_matters = 0

        for month in range(MONTHS_PER_YEAR - 1, num_months + 1, MONTHS_PER_YEAR):
            first_month_of_year = month + 1 - MONTHS_PER_YEAR
            salary = sum(ordinary_incomes[first_month_of_year : month + 1])
            rent = projection["Buy"]["Rental Income (Pre-Tax)"][
                first_month_of_year : month + 1
            ].sum()
            deduction = _deductible_mortgage_interest_for_the_year(projection, month)

            reported = (
                projection["Buy"]["Tax on Rental Income"].iloc[month]
                - projection["Buy"]["Mortgage Interest Deduction Savings"].iloc[month]
            )
            stacked = market_config.get_tax(
                month, salary + rent, ordinary_income_deduction=deduction
            ) - market_config.get_tax(month, salary)
            parallel = (
                market_config.get_additional_tax_from_additional_income(
                    month, salary, rent
                )
                - -TaxModule(market_config)
                .extra_tax_from(
                    month,
                    TaxableAmounts(ordinary_income=salary),
                    TaxableAmounts(ordinary_deductions=deduction),
                )
                .ordinary
            )
            assert reported == pytest.approx(stacked, abs=0.02)
            if stacked != pytest.approx(parallel, abs=0.02):
                years_where_stacking_matters += 1

        # a config whose brackets never bind would pass either way
        assert years_where_stacking_matters > 0

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
