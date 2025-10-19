import argparse
import datetime
import os
from typing import Any

import openpyxl
import pandas as pd

from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.core.calculator import Calculator
from rent_buy_invest.core.final_state import FinalState
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.io.experiment_writer import ExperimentWriter
from rent_buy_invest.io.io_utils import RentBuyInvestFileOpener
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

PRIMARY_HOME_CAP_GAINS_EXEMPTION = 250000


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rent_buy_invest",
        description="Calculates the long-term financial pros and cons of decisions related to renting a home, buying a home, and investing in the stock market.",
        epilog="See README for more details.",
    )
    parser.add_argument(
        "experiment_config",
        type=str,
        help="Path (from 'rent_buy_invest' directory) to experiment config file.",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        help="Name of the experiment. Output folder will be 'out/<experiment_name>/<timestamp>'; defaults to 'experiment'",
    )
    args = parser.parse_args()
    assert args.experiment_config.endswith(".yaml") or args.experiment.config_endswith(
        ".yml"
    ), "Experiment config file must end in '.yaml' or '.yml'"
    if not args.experiment_name:
        args.experiment_name = "unnamed_experiment"
    return args


def main() -> None:
    """Main method; entrypoint for this repo."""

    # get args; set up `--help` and `-h`
    args = _get_args()

    # load configs
    experiment_config = ExperimentConfig.parse(args.experiment_config)
    num_years = experiment_config.num_years
    market_config = experiment_config.market_config
    personal_config = experiment_config.personal_config
    rent_config = experiment_config.rent_config
    buy_config = experiment_config.buy_config
    start_date = experiment_config.start_date

    # initialize experiment writer
    experiment_writer = ExperimentWriter(args.experiment_name)
    # dump configs in output dir (to keep record of configs)
    experiment_writer.write_yaml("configs.yaml", experiment_config)
    # calculate initial state
    initial_state = InitialState.from_configs(
        buy_config, rent_config, market_config, personal_config
    )
    # dump initial state
    experiment_writer.write_xlsx_df(
        "initial_state.xlsx", initial_state.get_df(), num_header_rows=1
    )

    # project forward in time
    calculator = Calculator(
        buy_config,
        rent_config,
        market_config,
        personal_config,
        num_years,
        start_date,
        initial_state,
    )
    projection = calculator.calculate()
    experiment_writer.write_xlsx_df("projection.xlsx", projection, num_header_rows=2)

    # TODO handle short term gain too?
    assert num_years > 1
    # at the end, compare only post-tax values
    # buy side: need to sell house, and investments
    # the sale itself includes some deductible and non-deductible expenses, so we'll calculate that too
    # rent side: need to sell investments
    # First do buy case
    # Realistically you wouldn't sell all your investments at once...
    # you'd spread it out, and there's probably some optimal way to do that...
    # but here we assume all at once...
    # TODO maybe I should do it separately. After all, there may be a HUGE cap gains in one year, so doing it all at once may make it seem like buying is worse than it really is
    assert len(projection) % MONTHS_PER_YEAR == 1
    # get last year's annual income
    annual_income = sum(
        personal_config.get_ordinary_incomes(num_years * MONTHS_PER_YEAR)[
            -1 - MONTHS_PER_YEAR : -1
        ]
    )
    # get cap gains on investments if buying
    final_investments_if_buying = projection[("Buy", "Invested (Pre-Tax)")].iloc[-1]
    initial_investments_if_buying = projection[("Buy", "Invested (Pre-Tax)")].iloc[0]
    # TODO handle losses here and everywhere else. For now, just set gain to 0
    cap_gains_from_selling_investments_if_buying = max(
        final_investments_if_buying - initial_investments_if_buying, 0
    )
    # get cap gains on home
    # don't want to separately find tax for investments and home, since they don't contribute "proportionally"
    # due to tax bracketing. Find total cap gains, then calculate tax
    loan_amount = projection[("Buy", "Loan Amount")].iloc[-1]
    final_home_price = projection[("Buy", "Home Value")].iloc[-1]
    initial_home_price = projection[("Buy", "Home Value")].iloc[0]
    # some selling costs are immediately deductible from capital gains
    deductible_selling_costs = buy_config.get_deductible_selling_costs(final_home_price)
    nondeductible_selling_costs = buy_config.get_nondeductible_selling_costs(
        final_home_price
    )
    home_cost_basis = (
        initial_home_price + buy_config.get_part_of_basis_upfront_one_time_cost()
    )
    cap_gains_from_selling_home = max(
        (final_home_price - deductible_selling_costs) - home_cost_basis,
        0,
    )
    # calculate deduction here because it is separate for home vs investments
    if not buy_config.rental_income_config:
        home_cap_gains_exemption = min(
            PRIMARY_HOME_CAP_GAINS_EXEMPTION, cap_gains_from_selling_home
        )
        cap_gains_from_selling_home -= home_cap_gains_exemption
    total_cap_gains_if_buying = (
        cap_gains_from_selling_investments_if_buying + cap_gains_from_selling_home
    )
    # TODO create classes/methods for this
    num_months = num_years * MONTHS_PER_YEAR
    income_and_cap_gains_tax_if_buying = market_config.get_tax(
        num_months + 1,
        ordinary_income=annual_income,
        long_term_capital_gains=total_cap_gains_if_buying,
    )
    only_income_tax_if_buying = market_config.get_tax(
        num_months + 1, ordinary_income=annual_income
    )
    cap_gains_tax_if_buying = (
        income_and_cap_gains_tax_if_buying - only_income_tax_if_buying
    )
    wealth_if_buying = (
        -loan_amount
        + final_investments_if_buying
        + (final_home_price - deductible_selling_costs - nondeductible_selling_costs)
        - cap_gains_tax_if_buying
    )

    # Now do rent case
    final_investments_if_renting = projection[("Rent", "Invested (Pre-Tax)")].iloc[-1]
    initial_investments_if_renting = projection[("Rent", "Invested (Pre-Tax)")].iloc[0]
    cap_gains_from_selling_investments_if_renting = max(
        final_investments_if_renting - initial_investments_if_renting, 0
    )
    total_cap_gains_if_renting = cap_gains_from_selling_investments_if_renting
    income_and_cap_gains_tax_if_renting = market_config.get_tax(
        num_months + 1,
        ordinary_income=annual_income,
        long_term_capital_gains=total_cap_gains_if_renting,
    )
    only_income_tax_if_renting = market_config.get_tax(
        num_months + 1, ordinary_income=annual_income
    )
    cap_gains_tax_if_renting = (
        income_and_cap_gains_tax_if_renting - only_income_tax_if_renting
    )
    wealth_if_renting = final_investments_if_renting - cap_gains_tax_if_renting
    final_state = FinalState(
        wealth_if_renting=wealth_if_renting, wealth_if_buying=wealth_if_buying
    )
    experiment_writer.write_xlsx_df(
        "final_state.xlsx", final_state.get_df(), num_header_rows=1
    )


if __name__ == "__main__":
    main()
