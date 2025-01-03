import datetime

import pandas as pd

from rent_buy_invest.core.house_config import HouseConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.market_config import MarketConfig
from rent_buy_invest.core.rent_config import RentConfig
from rent_buy_invest.utils.data_utils import to_df
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR, increment_month

# PMI means Private Mortgage Insurance, and this is the mortgage insurance you'd get for a conventional
# (i.e., non-FHA) loan.
# LTV means loan-to-value, which is the ratio, at a given time, of the loan amount to the home value. The
# initial LTV is the same as the loan-to-purchase-price (LTPP), but the LTV can change over time (and generally
# decreases, since the loan is usually paid off and home values usually rise).
# This threshold is the threshold such that when the LTV at the time of home purchase (i.e., the LTPP)
# is above this threshold, PMI is required; if the LTPP is less than or equal to this threshold, no PMI is required.
# If PMI is required, the premium is set once and not recalculated again by default. If, however, during the mortgage
# term, the buyer thinks the LTV has dropped to 0.8 or below, the borrower can request a re-appraisal (which the
# borrower has to pay for) and if the resulting LTV is 0.8 or below, PMI is no longer required. By the way,
# as of Jan 25, 2024, the lender is supposed to automatically remove the PMI at 78% but the rule is that the borrower
# can demand to have it removed at 80%.
PMI_LTV_THRESHOLD = 0.8

# For FHA loans, the FHA requires FHA mortgage insurance (MI) if the loan-to-purchase-price (LTPP) is greater
# than this threshold. This FHA MI lasts for the ENTIRETY of the loan
FHA_MI_LTPP_THRESHOLD_FOR_LIFELONG_MORTGAGE_INSURANCE = 0.9

# If the LTPP is at or below FHA_MI_LTPP_THRESHOLD_FOR_LIFELONG_MORTGAGE_INSURANCE, the borrower must pay for FHA MI
# for this many months
FHA_MI_TERM_IF_BELOW_THRESHOLD = MONTHS_PER_YEAR * 11


class Calculator:
    def __init__(
        self,
        house_config: HouseConfig,
        rent_config: RentConfig,
        market_config: MarketConfig,
        num_months: int,
        start_date: datetime.date,
        initial_state: InitialState,
    ) -> None:
        self.house_config: HouseConfig = house_config
        self.rent_config: RentConfig = rent_config
        self.market_config: MarketConfig = market_config
        self.num_months: int = num_months
        self.start_date: datetime.date = start_date
        self.initial_state: InitialState = initial_state

    def calculate(self) -> pd.DataFrame:
        # Some housing costs/gains can be calculated independently at once
        home_values = self.house_config.get_monthly_home_values(self.num_months)
        house_monthly_costs_related_to_home_value = (
            self.house_config.get_home_value_related_monthly_costs(self.num_months)
        )
        house_monthly_costs_related_to_inflation = (
            self.house_config.get_inflation_related_monthly_costs(
                self.rent_config.annual_rent_inflation_rate, self.num_months
            )
        )

        # Some renting costs/gains can be calculated independently at once
        rent_monthly_costs = self.rent_config.get_monthly_costs_of_renting(
            self.num_months
        )

        # The remaining housing and rental costs/gains are calculated in the loop
        # which projects forward month by month
        mortgage_interests = []
        paid_toward_equity = []
        loan_amounts = []
        equities = []
        mortgage_insurances = []
        housing_monthly_surpluses = []
        rent_monthly_surpluses = []
        investment_values_if_renting = [
            self.initial_state.invested_in_market_if_renting
        ]  # NOTE: first value filled in
        investment_values_if_house = [0]  # NOTE: first value filed in

        loan_amount = self.house_config.initial_loan_amount
        monthly_mortgage_payment = self.house_config.get_monthly_mortgage_payment()
        mortgage_insurance_if_required = round(
            self.house_config.annual_mortgage_insurance_fraction
            * self.house_config.initial_loan_amount
            / MONTHS_PER_YEAR,
            2,
        )

        house_one_off_costs = []
        for month in range(self.num_months + 1):
            house_one_off_cost = 0

            loan_amounts.append(loan_amount)

            # mortgage interest cost
            mortgage_interest = round(
                loan_amount
                * self.house_config.mortgage_annual_interest_rate
                / MONTHS_PER_YEAR,
                2,
            )
            mortgage_interests.append(mortgage_interest)

            # mortgage equity payment and equity value
            if loan_amount == 0:
                # mortgage already paid off
                # no loan amount, so mortgage_interest is zero also
                toward_equity = 0
            elif loan_amount + mortgage_interest <= monthly_mortgage_payment:
                # final mortgage payment
                # paying interest on prev month and the remaining little loan amount
                toward_equity = loan_amount
            else:
                # regular mortgage payment
                toward_equity = round(monthly_mortgage_payment - mortgage_interest, 2)
            paid_toward_equity.append(toward_equity)
            equities.append(round(home_values[month] - loan_amount, 2))

            if not mortgage_interest:
                mortgage_insurance = 0
            elif not self.house_config.is_fha_loan:
                if loan_amount <= PMI_LTV_THRESHOLD * self.house_config.sale_price:
                    if mortgage_insurances and mortgage_insurances[-1] != 0:
                        house_one_off_cost += self.house_config.home_appraisal_cost
                    mortgage_insurance = 0
                else:
                    mortgage_insurance = mortgage_insurance_if_required
            else:
                if (
                    self.house_config.initial_loan_fraction
                    > FHA_MI_LTPP_THRESHOLD_FOR_LIFELONG_MORTGAGE_INSURANCE
                ):
                    mortgage_insurance = mortgage_insurance_if_required
                else:
                    if month // MONTHS_PER_YEAR < FHA_MI_TERM_IF_BELOW_THRESHOLD:
                        mortgage_insurance = mortgage_insurance_if_required
                    else:
                        mortgage_insurance = 0
            mortgage_insurances.append(mortgage_insurance)

            house_one_off_costs.append(house_one_off_cost)

            # monthly surplus from one option vs the other
            # investment_values_if_renting and investment_values_if_house have their
            # start-of-the-month value already filled in, so this calculates the value
            # at the end of the month.
            housing_monthly_payment = (
                house_monthly_costs_related_to_home_value[month]
                + house_monthly_costs_related_to_inflation[month]
                + mortgage_interest
                + toward_equity
                + mortgage_insurance
                + house_one_off_cost
            )
            rent_monthly_payment = rent_monthly_costs[month]
            gain_in_investment_if_renting = (
                self.market_config.get_pretax_monthly_wealth(
                    investment_values_if_renting[-1], 1
                )[1]
            )
            gain_in_investment_if_house = self.market_config.get_pretax_monthly_wealth(
                investment_values_if_house[-1], 1
            )[1]
            # Surplus from the perspective of renting
            surplus = round(housing_monthly_payment - rent_monthly_payment, 2)
            if surplus > 0:
                # if rent option has a relative surplus
                rent_monthly_surpluses.append(surplus)
                investment_values_if_renting.append(
                    round(gain_in_investment_if_renting + surplus, 2)
                )
                housing_monthly_surpluses.append(0)
                investment_values_if_house.append(gain_in_investment_if_house)
            elif surplus < 0:
                # if house option has a relative surplus
                # negate surplus to make it a positive from the perspective of housing
                surplus = -surplus
                rent_monthly_surpluses.append(0)
                investment_values_if_renting.append(gain_in_investment_if_renting)
                housing_monthly_surpluses.append(surplus)
                investment_values_if_house.append(
                    round(gain_in_investment_if_house + surplus, 2)
                )

            # update loan_amount for next iteration
            loan_amount -= toward_equity
            assert loan_amount >= 0, "Loan amount cannot be negative."
        # Pop last element from lists which have an extra item (starting value)
        investment_values_if_renting.pop()
        investment_values_if_house.pop()

        # RELIES on the fact that python dictionaries are now ordered
        cols = {
            # House: state
            "House: Non-house investment": investment_values_if_house,
            "House: House equity": equities,
            "House: Market value": home_values,
            "House: Loan amount": loan_amounts,
            # House: costs
            "House: Cost tied to market value": house_monthly_costs_related_to_home_value,
            "House: Cost tied to inflation": house_monthly_costs_related_to_inflation,
            "House: Mortgage Insurance": mortgage_insurances,
            "House: Mortgage interest payment": mortgage_interests,
            "House: Mortgage equity payment": paid_toward_equity,
            "House: One-off costs": house_one_off_costs,
            # black formats the following line in an easy-to-misread way
            # fmt: off
            "House: Mortgage payment": [i + e for i, e in zip(mortgage_interests, paid_toward_equity)],
            # fmt: on
            # House: relative surplus
            "House: Surplus (vs renting)": housing_monthly_surpluses,
            # Rent: state
            "Rent: Investment": investment_values_if_renting,
            # Rent: costs
            "Rent: Cost tied to inflation": rent_monthly_costs,
            # Rent: relative surplus
            "Rent: Surplus (vs buying house)": rent_monthly_surpluses,
        }
        rows = []
        date = self.start_date
        for _ in range(self.num_months + 1):
            rows.append(date.strftime("%b %d, %Y"))
            date = increment_month(date)
        return to_df(cols, rows, multi_col=True)
