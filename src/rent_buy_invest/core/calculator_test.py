from copy import deepcopy

import pytest

from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.experiment_config_test import TestExperimentConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.calculator import Calculator
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.mortgage_insurance import PMI_LTV_THRESHOLD
from rent_buy_invest.core.tax import (
    MAX_MORTGAGE_BALANCE_ON_WHICH_INTEREST_IS_DEDUCTIBLE,
    TaxableAmounts,
    TaxModule,
)
from rent_buy_invest.io import io_utils
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

    def test_calculate_handles_a_month_where_both_worlds_cost_the_same(self) -> None:
        """A month with no surplus on either side still produces a row.

        The loop used to handle only a positive or a negative surplus. A tie to the
        cent appended nothing, so every column after it came up one row short and
        building the projection raised. Here one month's rent is set to exactly
        what buying costs that month, which forces the tie.
        """
        month = 5
        baseline = Calculator(
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
        ).calculate()
        # the rent that makes this month's two net costs equal: the gap between
        # them is exactly the pair of surpluses
        rent_costs = list(baseline["Rent"]["Costs Tied to Inflation"])
        rent_costs[month] = round(
            rent_costs[month]
            + baseline["Rent"]["Surplus"].iloc[month]
            - baseline["Buy"]["Surplus"].iloc[month],
            2,
        )
        rent_config = deepcopy(EXPERIMENT_CONFIG.rent_config)
        rent_config.get_monthly_costs_of_renting = lambda num_months: rent_costs

        projection = Calculator(
            EXPERIMENT_CONFIG.buy_config,
            rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.personal_config,
            EXPERIMENT_CONFIG.num_years,
            EXPERIMENT_CONFIG.start_date,
            InitialState.from_configs(
                EXPERIMENT_CONFIG.buy_config,
                rent_config,
                EXPERIMENT_CONFIG.market_config,
                EXPERIMENT_CONFIG.personal_config,
            ),
        ).calculate()

        assert projection.shape[0] == EXPERIMENT_CONFIG.num_years * MONTHS_PER_YEAR + 1
        assert projection["Rent"]["Surplus"].iloc[month] == 0
        assert projection["Buy"]["Surplus"].iloc[month] == 0
        # up to and including the tie nothing else changed, so the accounts match
        # the baseline; the month after, each has only grown, with no deposit
        for world in ["Rent", "Buy"]:
            invested = projection[world]["Invested (Pre-Tax)"]
            assert invested.iloc[: month + 1].equals(
                baseline[world]["Invested (Pre-Tax)"].iloc[: month + 1]
            )
            assert invested.iloc[month + 1] == (
                EXPERIMENT_CONFIG.market_config.get_pretax_monthly_wealth(
                    invested.iloc[month], 1
                )[1]
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


def _staircase_long_term_capital_gains_brackets() -> list[dict]:
    """Long-term capital gains brackets whose rate rises every $10,000.

    The shared test config taxes gains at one flat 10% from $44,625 to $492,300,
    and every year of its projection sits inside that band -- so where the gains
    stack cannot change what they cost, and a test of the stacking passes no
    matter what the base is. A small step everywhere makes any shift in the base
    change the tax.
    """
    step = 10_000.0
    num_steps = 300
    brackets = [
        {"upper_limit": step * (i + 1), "tax_rate": 0.0005 * i}
        for i in range(num_steps)
    ]
    brackets.append({"upper_limit": float("inf"), "tax_rate": 0.0005 * num_steps})
    return brackets


def _calculator_with_dividends(
    dividend_yield: float, long_term_capital_gains_brackets: list[dict] | None = None
) -> Calculator:
    """The shared fixture with part of the market return paid out as dividends.

    Optionally with different long-term capital gains brackets; the ordinary
    brackets are always the shared fixture's.
    """
    market_kwargs = deepcopy(
        io_utils.read_yaml(
            "rent_buy_invest/core/test_resources/test-market-config.yaml"
        )
    )
    market_kwargs["market_dividend_yield"] = dividend_yield
    if long_term_capital_gains_brackets is not None:
        market_kwargs["tax_brackets"][
            "long_term_capital_gains_tax_brackets"
        ] = long_term_capital_gains_brackets
    market_config = MarketConfig(**market_kwargs)
    return Calculator(
        EXPERIMENT_CONFIG.buy_config,
        EXPERIMENT_CONFIG.rent_config,
        market_config,
        EXPERIMENT_CONFIG.personal_config,
        EXPERIMENT_CONFIG.num_years,
        EXPERIMENT_CONFIG.start_date,
        InitialState.from_configs(
            EXPERIMENT_CONFIG.buy_config,
            EXPERIMENT_CONFIG.rent_config,
            market_config,
            EXPERIMENT_CONFIG.personal_config,
        ),
    )


class TestCalculatorDividends:
    def test_calculate_charges_no_dividend_tax_at_a_zero_yield(self) -> None:
        """The whole return is price appreciation, deferred until the sale."""
        projection = _calculator_with_dividends(0.0).calculate()

        assert (projection["Rent"]["Dividend Tax"] == 0).all()
        assert (projection["Buy"]["Dividend Tax"] == 0).all()

    def test_calculate_settles_dividend_tax_once_a_year(self) -> None:
        """Like every other tax here, it lands in the last month of each year."""
        projection = _calculator_with_dividends(0.02).calculate()

        for world in ["Rent", "Buy"]:
            taxes = projection[world]["Dividend Tax"]
            assert (taxes > 0).any(), f"{world} never paid dividend tax"
            for month, tax in enumerate(taxes):
                if month % MONTHS_PER_YEAR != MONTHS_PER_YEAR - 1:
                    assert tax == 0, f"{world} month {month} settled tax mid-year"

    def test_calculate_takes_dividend_tax_out_of_the_balance(self) -> None:
        """Each month: grow, add the deposit, pay the dividend tax, and nothing else."""
        calculator = _calculator_with_dividends(0.02)
        projection = calculator.calculate()

        for world in ["Rent", "Buy"]:
            invested = projection[world]["Invested (Pre-Tax)"]
            for month in range(projection.shape[0] - 1):
                grown = calculator.market_config.get_pretax_monthly_wealth(
                    invested.iloc[month], 1
                )[1]
                expected = round(
                    grown
                    + projection[world]["Surplus"].iloc[month]
                    - projection[world]["Dividend Tax"].iloc[month],
                    2,
                )
                assert invested.iloc[month + 1] == pytest.approx(expected, abs=0.01)

    def test_calculate_does_not_tax_dividends_again_at_the_end(self) -> None:
        """The whole point of growing the basis by the dividend net of its tax.

        Pay out the ENTIRE return as dividends and every dollar an account earns is
        taxed in the year it arrives, so by the horizon there is no unrealized gain
        left: the balance and the basis agree. Taxing the dividend and leaving the
        basis alone would tax the same dollars twice at the sale, and adding the
        gross dividend would invent a loss.
        """
        total_return = EXPERIMENT_CONFIG.market_config.market_rate_of_return
        assert total_return > 0
        projection = _calculator_with_dividends(total_return).calculate()

        for world in ["Rent", "Buy"]:
            assert projection[world]["Dividend Tax"].sum() > 0
            # the dividends counted are only those settled at a year boundary, so
            # compare at the last month whose year was settled
            last_settled = (
                (projection.shape[0] - 1) // MONTHS_PER_YEAR
            ) * MONTHS_PER_YEAR
            assert projection[world]["Invested (Pre-Tax)"].iloc[
                last_settled
            ] == pytest.approx(
                projection[world]["Invested Cost Basis"].iloc[last_settled], abs=1.0
            )

    def test_calculate_stacks_buying_dividends_on_rent_and_the_deduction(
        self,
    ) -> None:
        """The buying world's dividends are charged where its other income left it.

        That world's year is salary plus rent received less the mortgage interest
        deduction, and the dividends land on top of that. Charging them against
        salary alone would tax them in a bracket they never reach -- silently, and
        only in years where the difference moves a bracket boundary. Hence the
        staircase brackets: under the shared config's flat band it never does.
        """
        calculator = _calculator_with_dividends(
            0.02, _staircase_long_term_capital_gains_brackets()
        )
        projection = calculator.calculate()
        market_config = calculator.market_config
        tax_module = calculator.tax_module
        incomes = EXPERIMENT_CONFIG.personal_config.get_ordinary_incomes(
            projection.shape[0] - 1
        )

        growth = 0.0
        years_where_the_base_matters = 0
        for month in range(projection.shape[0]):
            balance = projection["Buy"]["Invested (Pre-Tax)"].iloc[month]
            growth += market_config.get_pretax_monthly_wealth(balance, 1)[1] - balance
            if month % MONTHS_PER_YEAR != MONTHS_PER_YEAR - 1:
                continue
            first_month_of_year = month + 1 - MONTHS_PER_YEAR
            salary = sum(incomes[first_month_of_year : month + 1])
            rent_received = projection["Buy"]["Rental Income (Pre-Tax)"][
                first_month_of_year : month + 1
            ].sum()
            deduction = _deductible_mortgage_interest_for_the_year(projection, month)
            dividends = market_config.get_dividends_from_growth(growth)
            growth = 0.0

            dividend_layer = TaxableAmounts(long_term_capital_gains=dividends)
            stacked_on_the_year = tax_module.extra_tax_from(
                month,
                TaxableAmounts(
                    ordinary_income=salary + rent_received,
                    ordinary_deductions=deduction,
                ),
                dividend_layer,
            ).long_term_capital_gain
            stacked_on_salary_alone = tax_module.extra_tax_from(
                month, TaxableAmounts(ordinary_income=salary), dividend_layer
            ).long_term_capital_gain
            assert projection["Buy"]["Dividend Tax"].iloc[month] == pytest.approx(
                stacked_on_the_year, abs=0.01
            )
            if stacked_on_the_year != pytest.approx(stacked_on_salary_alone, abs=0.01):
                years_where_the_base_matters += 1

        # a config where the base never moved a bracket would pass vacuously
        assert years_where_the_base_matters > 0
