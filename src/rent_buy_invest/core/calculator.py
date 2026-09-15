import datetime

import pandas as pd

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.configs.rent_config import RentConfig
from rent_buy_invest.core.amortization import compute_loan_amortization_schedule
from rent_buy_invest.core.initial_state import InitialState
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
        investment_values_if_renting = [
            self.initial_state.invested_if_renting
        ]  # NOTE: first value filled in
        investment_values_if_buying = [0]  # NOTE: first value filed in
        # Cost basis: every dollar paid into the account, plus dividends that were
        # already taxed and stayed invested -- none of which is gain when the
        # account is cashed out. Seeded and popped the same way as the balances, so
        # the two cannot fall out of step.
        invested_cost_bases_if_renting = [self.initial_state.invested_if_renting]
        invested_cost_bases_if_buying = [0]
        dividend_taxes_if_renting = []
        dividend_taxes_if_buying = []
        # What each account earned since the last year boundary. Dividends are a
        # share of this, so it has to be accumulated as the year runs rather than
        # inferred from the balances, which also move on deposits.
        growth_if_renting_this_year = 0.0
        growth_if_buying_this_year = 0.0

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
            # Both accounts grow for the month. This runs before tax because the
            # year's dividends are a share of this growth.
            grown_if_renting = self.market_config.get_pretax_monthly_wealth(
                investment_values_if_renting[-1], 1
            )[1]
            grown_if_buying = self.market_config.get_pretax_monthly_wealth(
                investment_values_if_buying[-1], 1
            )[1]
            growth_if_renting_this_year += (
                grown_if_renting - investment_values_if_renting[-1]
            )
            growth_if_buying_this_year += (
                grown_if_buying - investment_values_if_buying[-1]
            )

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

                # How much of this year's growth was paid out as dividends. Nothing
                # is added to the balance here: it already grew at the full market
                # return, dividends included. What changes is when those dollars
                # are taxed: now, instead of at the sale.
                #
                # Qualified dividends are taxed at the long-term capital gains
                # rates, and which of those rates applies depends on the rest of
                # the year's taxable income, which fills the lower brackets first.
                # For the renter that is salary. For the buyer it is salary, plus
                # any rental income, less the mortgage interest deduction -- which
                # is why `position` was advanced past all three above.
                #
                # The tax comes out of the balance below. What is left of the
                # dividends stays invested like any other money, and counts toward
                # the basis so it is not taxed a second time at the sale.
                get_dividends = self.market_config.get_dividends_from_growth
                dividends_if_renting = get_dividends(growth_if_renting_this_year)
                dividends_if_buying = get_dividends(growth_if_buying_this_year)
                dividend_tax_if_renting = self.tax_module.extra_tax_from(
                    month,
                    TaxableAmounts(ordinary_income=annual_income),
                    TaxableAmounts(long_term_capital_gains=dividends_if_renting),
                ).long_term_capital_gain
                dividend_tax_if_buying = self.tax_module.extra_tax_from(
                    month,
                    position,
                    TaxableAmounts(long_term_capital_gains=dividends_if_buying),
                ).long_term_capital_gain
                reinvested_if_renting = round(
                    dividends_if_renting - dividend_tax_if_renting, 2
                )
                reinvested_if_buying = round(
                    dividends_if_buying - dividend_tax_if_buying, 2
                )
                growth_if_renting_this_year = 0.0
                growth_if_buying_this_year = 0.0
            else:
                rental_income_tax = 0
                mortgage_interest_deduction_saving = 0
                dividend_tax_if_renting = dividend_tax_if_buying = 0.0
                reinvested_if_renting = reinvested_if_buying = 0.0
            dividend_taxes_if_renting.append(dividend_tax_if_renting)
            dividend_taxes_if_buying.append(dividend_tax_if_buying)
            mortgage_interest_deduction_savings.append(
                mortgage_interest_deduction_saving
            )
            rental_income_taxes.append(rental_income_tax)

            # mortgage equity payment and equity value
            toward_equity = mortgage_amortization_schedule.principal_payments[month]
            equities.append(round(home_values[month] - loan_amount, 2))

            # monthly surplus from one option vs the other
            # investment_values_if_renting and investment_values_if_buying have their
            # start-of-the-month value already filled in, so this calculates the value
            # at the end of the month.
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

            # The dividend tax is paid out of the account, so it lowers the balance
            # and nothing else. The dividend left after that tax stays invested and
            # has already been taxed, so it is basis, not gain, when the account is
            # finally sold.
            investment_values_if_renting.append(
                round(
                    grown_if_renting + deposit_if_renting - dividend_tax_if_renting,
                    2,
                )
            )
            invested_cost_bases_if_renting.append(
                round(
                    invested_cost_bases_if_renting[-1]
                    + deposit_if_renting
                    + reinvested_if_renting,
                    2,
                )
            )
            investment_values_if_buying.append(
                round(
                    grown_if_buying + deposit_if_buying - dividend_tax_if_buying,
                    2,
                )
            )
            invested_cost_bases_if_buying.append(
                round(
                    invested_cost_bases_if_buying[-1]
                    + deposit_if_buying
                    + reinvested_if_buying,
                    2,
                )
            )

            assert loan_amount >= 0, "Loan amount cannot be negative."
        # Pop last element from lists which have an extra item (starting value)
        investment_values_if_renting.pop()
        investment_values_if_buying.pop()
        invested_cost_bases_if_renting.pop()
        invested_cost_bases_if_buying.pop()

        # RELIES on the fact that python dictionaries are now ordered
        cols = {
            # Buy: state
            "Buy: Invested (Pre-Tax)": investment_values_if_buying,
            "Buy: Invested Cost Basis": invested_cost_bases_if_buying,
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
            "Buy: Dividend Tax": dividend_taxes_if_buying,
            # Buy: relative surplus
            "Buy: Surplus": housing_monthly_surpluses,
            # Rent: state
            "Rent: Invested (Pre-Tax)": investment_values_if_renting,
            "Rent: Invested Cost Basis": invested_cost_bases_if_renting,
            # Rent: costs
            "Rent: Costs Tied to Inflation": rent_monthly_costs,
            "Rent: Dividend Tax": dividend_taxes_if_renting,
            # Rent: relative surplus
            "Rent: Surplus": rent_monthly_surpluses,
        }
        rows = []
        date = self.start_date
        for _ in range(num_months + 1):
            rows.append(date.strftime("%b %d, %Y"))
            date = increment_month(date)
        return to_df(cols, rows, multi_col=True)
