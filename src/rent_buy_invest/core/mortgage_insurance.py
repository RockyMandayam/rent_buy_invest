from dataclasses import dataclass

from rent_buy_invest.core.amortization import LoanAmortizationSchedule
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

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


@dataclass(frozen=True)
class MortgageInsuranceSchedule:
    """Per-month mortgage insurance cost for a home loan.

    The two lists are of equal length and indexed by month, matching the
    ``LoanAmortizationSchedule`` the cost was derived from. For month ``m``,
    ``premiums[m]`` is that month's insurance premium, and ``appraisal_costs[m]``
    is any one-off cost incurred that month -- non-zero only in the single month
    a conventional borrower pays for the re-appraisal that drops their PMI.
    """

    premiums: list[float]
    appraisal_costs: list[float]


def compute_mortgage_insurance_schedule(
    loan_amortization_schedule: LoanAmortizationSchedule,
    is_fha_loan: bool,
    initial_loan_amount: float,
    initial_loan_fraction: float,
    purchase_price: float,
    annual_mortgage_insurance_fraction: float,
    home_appraisal_cost: float,
) -> MortgageInsuranceSchedule:
    """Project mortgage insurance over the months ``loan_amortization_schedule`` covers.

    The premium, when one is owed, is a fixed fraction of the *original* loan
    amount; it is set at closing and never recalculated. What changes month to
    month is only whether it is owed at all, and the rule for that depends on the
    kind of loan:

    - **Conventional:** PMI is owed while the balance is above
      ``PMI_LTV_THRESHOLD`` of the purchase price. The month the balance first
      falls to or below it, the borrower pays ``home_appraisal_cost`` for the
      re-appraisal that proves the new LTV, and owes no PMI from then on.
    - **FHA:** if the loan started above
      ``FHA_MI_LTPP_THRESHOLD_FOR_LIFELONG_MORTGAGE_INSURANCE`` of the purchase
      price, MI is owed for the life of the loan. Otherwise it is owed for the
      first ``FHA_MI_TERM_IF_BELOW_THRESHOLD`` months only.

    Either way, nothing is owed once the loan is no longer accruing interest.
    """
    premium_if_required = round(
        annual_mortgage_insurance_fraction * initial_loan_amount / MONTHS_PER_YEAR,
        2,
    )

    premiums: list[float] = []
    appraisal_costs: list[float] = []

    for month, loan_amount in enumerate(loan_amortization_schedule.starting_balances):
        appraisal_cost = 0

        if not loan_amortization_schedule.interest_payments[month]:
            # no interest accruing means no live loan left to insure
            premium = 0
        elif not is_fha_loan:
            if loan_amount <= PMI_LTV_THRESHOLD * purchase_price:
                if premiums and premiums[-1] != 0:
                    # first month that PMI can be dropped: the borrower pays for the
                    # re-appraisal that proves the LTV
                    appraisal_cost = home_appraisal_cost
                premium = 0
            else:
                premium = premium_if_required
        elif (
            initial_loan_fraction
            > FHA_MI_LTPP_THRESHOLD_FOR_LIFELONG_MORTGAGE_INSURANCE
        ):
            premium = premium_if_required
        elif month < FHA_MI_TERM_IF_BELOW_THRESHOLD:
            premium = premium_if_required
        else:
            premium = 0

        premiums.append(premium)
        appraisal_costs.append(appraisal_cost)

    return MortgageInsuranceSchedule(
        premiums=premiums,
        appraisal_costs=appraisal_costs,
    )
