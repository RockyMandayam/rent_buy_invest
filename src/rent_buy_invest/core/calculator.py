import datetime

import pandas as pd

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.configs.rent_config import RentConfig
from rent_buy_invest.core.amortization import compute_loan_amortization_schedule
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.market_account import compute_market_account_schedule
from rent_buy_invest.core.mortgage_insurance import compute_mortgage_insurance_schedule
from rent_buy_invest.core.tax import TaxableAmounts, TaxModule
from rent_buy_invest.utils.data_utils import to_df
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR, avg, increment_month


class Calculator:
    def __init__(
        self,
        buy_config: BuyConfig,
        rent_config: RentConfig,
        market_config: MarketConfig,
        personal_config: PersonalConfig,
        num_years: int,
        start_date: datetime.date,
        initial_state: InitialState,
    ) -> None:
        self.buy_config: BuyConfig = buy_config
        self.rent_config: RentConfig = rent_config
        self.market_config: MarketConfig = market_config
        self.personal_config: PersonalConfig = personal_config
        self.num_years: int = num_years
        self.start_date: datetime.date = start_date
        self.initial_state: InitialState = initial_state
        self.tax_module: TaxModule = TaxModule(market_config)

    def calculate(self) -> pd.DataFrame:
        num_months = self.num_years * MONTHS_PER_YEAR

        # Some housing costs/gains can be calculated independently at once
        home_values = self.buy_config.get_monthly_home_values(num_months)
        home_monthly_costs_related_to_home_value = (
            self.buy_config.get_home_value_related_monthly_costs(
                self.market_config.annual_inflation_rate, num_months
            )
        )
        home_monthly_costs_related_to_inflation = (
            self.buy_config.get_inflation_related_monthly_costs(
                self.market_config.annual_inflation_rate, num_months
            )
        )
        home_monthly_rental_incomes = self.buy_config.get_monthly_rental_incomes(
            num_months
        )
        # Charged on rent collected, so it tracks the income above rather than the
        # home's value, and is zero whenever no rent is coming in.
        if self.buy_config.rental_income_config:
            home_monthly_management_fees = (
                self.buy_config.rental_income_config.get_monthly_management_fees(
                    num_months
                )
            )
        else:
            home_monthly_management_fees = [0.0] * (num_months + 1)

        # Projected ordinary income (used only for tax projection purposes)
        ordinary_incomes = self.personal_config.get_ordinary_incomes(num_months)

        # Some renting costs/gains can be calculated independently at once
        rent_monthly_costs = self.rent_config.get_monthly_costs_of_renting(num_months)

        # The remaining housing and rental costs/gains are calculated in the loop
        # which projects forward month by month
        mortgage_interest_deduction_savings = []
        equities = []
        rental_income_taxes = []
        housing_monthly_surpluses = []
        rent_monthly_surpluses = []
        # For each tax year, the rest of each world's taxable income, which its
        # dividends are taxed on top of.
        taxable_income_before_dividends_if_renting = []
        taxable_income_before_dividends_if_buying = []

        monthly_mortgage_payment = self.buy_config.get_monthly_mortgage_payment()
        mortgage_amortization_schedule = compute_loan_amortization_schedule(
            self.buy_config.initial_loan_amount,
            self.buy_config.mortgage_annual_interest_rate,
            monthly_mortgage_payment,
            num_months,
        )
        mortgage_insurance_schedule = compute_mortgage_insurance_schedule(
            mortgage_amortization_schedule,
            self.buy_config.is_fha_loan,
            self.buy_config.initial_loan_amount,
            self.buy_config.initial_loan_fraction,
            self.buy_config.purchase_price,
            self.buy_config.annual_mortgage_insurance_fraction,
            self.buy_config.home_appraisal_cost,
        )
        mortgage_insurances = mortgage_insurance_schedule.premiums
        buy_one_off_costs = mortgage_insurance_schedule.appraisal_costs

        for month in range(num_months + 1):
            loan_amount = mortgage_amortization_schedule.starting_balances[month]
            mortgage_interest = mortgage_amortization_schedule.interest_payments[month]
            # The year's ordinary-income tax adjustments -- rent received and the
            # mortgage interest deduction -- are settled together at the year
            # boundary, because they stack on each other.
            if month % MONTHS_PER_YEAR == (MONTHS_PER_YEAR - 1):
                mortgage_interest_for_the_year = sum(
                    mortgage_amortization_schedule.interest_payments[
                        month + 1 - MONTHS_PER_YEAR : month + 1
                    ]
                )
                avg_loan_amount = avg(
                    mortgage_amortization_schedule.starting_balances[
                        month + 1 - MONTHS_PER_YEAR : month + 1
                    ]
                )
                annual_income = sum(
                    ordinary_incomes[month + 1 - MONTHS_PER_YEAR : month + 1]
                )
                annual_rental_income = sum(
                    home_monthly_rental_incomes[month + 1 - MONTHS_PER_YEAR : month + 1]
                )
                deductible_mortgage_interest = (
                    self.tax_module.deductible_mortgage_interest(
                        mortgage_interest_for_the_year, avg_loan_amount
                    )
                )
                # The year has two ordinary-income adjustments, and they are not
                # independent: rent RAISES taxable income and the deduction LOWERS
                # it, so whichever is charged second lands in the bracket the first
                # one moved you to. Working each out from salary alone -- which is
                # what this did until now -- charges the rent and credits the
                # deduction as if the other had not happened, and prices some of
                # each in a bracket the year never reaches.
                #
                # The convention here is the one a tax return follows: all income
                # first, then deductions come off the top of it.
                # Both adjustments are ordinary income, and only their combined
                # effect on the year is a fact -- splitting it between the two
                # reported columns is a convention. The convention is the one a
                # tax return follows, so the position accumulates: income first,
                # then the deduction off the top of it.
                position = TaxableAmounts(ordinary_income=annual_income)
                rent_received = TaxableAmounts(ordinary_income=annual_rental_income)
                rental_income_tax = self.tax_module.extra_tax_from(
                    month, position, rent_received
                ).ordinary
                position = position + rent_received
                mortgage_interest_deduction = TaxableAmounts(
                    ordinary_deductions=deductible_mortgage_interest
                )
                mortgage_interest_deduction_saving = -self.tax_module.extra_tax_from(
                    month, position, mortgage_interest_deduction
                ).ordinary
                position = position + mortgage_interest_deduction

                # Dividends are taxed on top of the rest of the year's taxable
                # income, which fills the lower brackets first. For the renter that
                # is salary. For the buyer it is salary, plus any rental income,
                # less the mortgage interest deduction -- which is why `position`
                # was advanced past all three above.
                taxable_income_before_dividends_if_renting.append(
                    TaxableAmounts(ordinary_income=annual_income)
                )
                taxable_income_before_dividends_if_buying.append(position)
            else:
                rental_income_tax = 0
                mortgage_interest_deduction_saving = 0
            mortgage_interest_deduction_savings.append(
                mortgage_interest_deduction_saving
            )
            rental_income_taxes.append(rental_income_tax)

            # mortgage equity payment and equity value
            toward_equity = mortgage_amortization_schedule.principal_payments[month]
            equities.append(round(home_values[month] - loan_amount, 2))

            # monthly surplus from one option vs the other
            # The deduction saving is money the buyer does not send the IRS, so it
            # lands here as a negative cost, in the same year-boundary month the
            # rental income tax beside it lands in. It is zero in every other month.
            housing_monthly_cost = (
                home_monthly_costs_related_to_home_value[month]
                + home_monthly_costs_related_to_inflation[month]
                + mortgage_interest
                + toward_equity
                + mortgage_insurance_schedule.premiums[month]
                + mortgage_insurance_schedule.appraisal_costs[month]
                + home_monthly_management_fees[month]
                + rental_income_taxes[month]
                - mortgage_interest_deduction_savings[month]
            )
            housing_monthly_income = home_monthly_rental_incomes[month]
            housing_net_monthly_cost = housing_monthly_cost - housing_monthly_income
            rent_monthly_cost = rent_monthly_costs[month]
            rent_monthly_income = 0
            rent_net_monthly_cost = rent_monthly_cost - rent_monthly_income
            # Surplus from the perspective of renting
            surplus = round(housing_net_monthly_cost - rent_net_monthly_cost, 2)
            # Only the cheaper world has money spare to put in, so at most one of
            # these is non-zero. A tie to the cent leaves both at zero; rare, but
            # every list still needs its row that month.
            deposit_if_renting = surplus if surplus > 0 else 0
            deposit_if_buying = -surplus if surplus < 0 else 0
            rent_monthly_surpluses.append(deposit_if_renting)
            housing_monthly_surpluses.append(deposit_if_buying)

            assert loan_amount >= 0, "Loan amount cannot be negative."

        # The market accounts are worked out after the loop because nothing above
        # depends on them: the dividend tax is paid out of each account, never out
        # of the housing costs that decide the surplus. Each month's surplus is the
        # cheaper world's deposit, and the dearer world deposits nothing.
        #
        # The renting world opens with everything buying would have cost up front,
        # all of it basis: it is money paid in, not gain. The buying world opens
        # empty, its money having gone into the home.
        market_account_if_renting = compute_market_account_schedule(
            opening_balance=self.initial_state.invested_if_renting,
            opening_cost_basis=self.initial_state.invested_if_renting,
            monthly_deposits=rent_monthly_surpluses,
            taxable_income_before_dividends_by_year=(
                taxable_income_before_dividends_if_renting
            ),
            market_config=self.market_config,
            tax_module=self.tax_module,
        )
        market_account_if_buying = compute_market_account_schedule(
            opening_balance=0.0,
            opening_cost_basis=0.0,
            monthly_deposits=housing_monthly_surpluses,
            taxable_income_before_dividends_by_year=(
                taxable_income_before_dividends_if_buying
            ),
            market_config=self.market_config,
            tax_module=self.tax_module,
        )

        # RELIES on the fact that python dictionaries are now ordered
        cols = {
            # Buy: state
            "Buy: Invested (Pre-Tax)": market_account_if_buying.balances,
            "Buy: Invested Cost Basis": market_account_if_buying.cost_bases,
            "Buy: Home Equity": equities,
            "Buy: Home Value": home_values,
            "Buy: Loan Amount": mortgage_amortization_schedule.starting_balances,
            # Buy: costs
            "Buy: Costs Tied to Home Value": home_monthly_costs_related_to_home_value,
            "Buy: Costs Tied to Inflation": home_monthly_costs_related_to_inflation,
            "Buy: Management Fee": home_monthly_management_fees,
            "Buy: Mortgage Insurance": mortgage_insurances,
            "Buy: Mortgage Interest Payment": mortgage_amortization_schedule.interest_payments,
            "Buy: Mortgage Equity Payment": mortgage_amortization_schedule.principal_payments,
            "Buy: Mortgage Interest Deduction Savings": mortgage_interest_deduction_savings,
            "Buy: One-Off Costs": buy_one_off_costs,
            # black formats the following line in an easy-to-misread way
            # fmt: off
            "Buy: Mortgage Payment": [i + e for i, e in zip(mortgage_amortization_schedule.interest_payments, mortgage_amortization_schedule.principal_payments)],
            # fmt: on
            # TODO rental income's effect on your taxable income and therefore brackets and deductions savings
            "Buy: Rental Income (Pre-Tax)": home_monthly_rental_incomes,
            "Buy: Tax on Rental Income": rental_income_taxes,
            "Buy: Dividend Tax": market_account_if_buying.dividend_taxes,
            # Buy: relative surplus
            "Buy: Surplus": housing_monthly_surpluses,
            # Rent: state
            "Rent: Invested (Pre-Tax)": market_account_if_renting.balances,
            "Rent: Invested Cost Basis": market_account_if_renting.cost_bases,
            # Rent: costs
            "Rent: Costs Tied to Inflation": rent_monthly_costs,
            "Rent: Dividend Tax": market_account_if_renting.dividend_taxes,
            # Rent: relative surplus
            "Rent: Surplus": rent_monthly_surpluses,
        }
        rows = []
        date = self.start_date
        for _ in range(num_months + 1):
            rows.append(date.strftime("%b %d, %Y"))
            date = increment_month(date)
        return to_df(cols, rows, multi_col=True)
