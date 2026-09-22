import argparse

from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.core.calculator import Calculator
from rent_buy_invest.core.final_state import FinalState
from rent_buy_invest.core.home_sale import HomeSale, compute_home_sale
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.core.rental_vs_invest_experiment import (
    RentalVsInvestExperiment,
)
from rent_buy_invest.core.tax import TaxableAmounts, TaxModule
from rent_buy_invest.io.experiment_writer import ExperimentWriter
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR


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
    assert args.experiment_config.endswith(".yaml") or args.experiment_config.endswith(
        ".yml"
    ), "Experiment config file must end in '.yaml' or '.yml'"
    if not args.experiment_name:
        args.experiment_name = "unnamed_experiment"
    return args


def _cap_gains_from_selling_investments(
    market_balance: float, investment_cost_basis: float
) -> float:
    """Gain on a market account, in dollars: its balance less its cost basis.

    The basis is tracked month by month in ``Calculator`` rather than inferred
    here. It is the opening balance, **plus every deposit**, plus every dividend
    that was already taxed in its own year and stayed invested. None of that is
    money you made at the sale: the deposits are your own money, and the
    dividends have been taxed once already. Leaving either out taxes you twice.

    Losses are floored at zero: the tax layer has no way to use them yet.
    """
    # NOTE you cannot deduct losses for a primary residence property...
    return max(market_balance - investment_cost_basis, 0)


def _liquidate_rent_vs_buy(
    *,
    market_balance_if_renting: float,
    investment_cost_basis_if_renting: float,
    market_balance_if_buying: float,
    investment_cost_basis_if_buying: float,
    home_sale: HomeSale,
    loan_balance: float,
    is_a_home_you_lived_in: bool,
    personal_config: PersonalConfig,
    tax_module: TaxModule,
    num_years: int,
) -> FinalState:
    """Cash out both worlds at the horizon, so their wealth is comparable.

    An unsold home and an untaxed investment account are not comparable wealth,
    so each world sells everything it holds and pays the tax on doing so. The
    renting world holds one market account. The buying world holds a market
    account and the home, and pays off what is left of the loan.

    The buying world's two gains are taxed together, as one year's long-term
    capital gains, not separately: brackets are progressive, so two gains taxed
    apart would cost less than their total taxed as one.

    Every dollar figure is the value at the horizon: the last month of the
    projection. Keyword-only, because most of them are plain dollar amounts that
    would be easy to pass in the wrong order.

    Args:
        market_balance_if_renting: the renting world's market account balance.
        investment_cost_basis_if_renting: that account's cost basis.
        market_balance_if_buying: the buying world's market account balance.
        investment_cost_basis_if_buying: that account's cost basis.
        home_sale: what selling the home brings in, and what it cost.
        loan_balance: what is still owed on the mortgage, paid off from the sale.
        is_a_home_you_lived_in: whether the home's gain gets the exclusion for a
            home you lived in. A home with rental income does not.
        personal_config: whose salary the sale's gains stack on.
        tax_module: prices the sale's tax.
        num_years: the length of the projection, in years.
    """
    # TODO handle short term gain too?
    assert num_years > 1
    # at the end, compare only post-tax values
    # buy side: need to sell house, and investments
    # the sale itself has selling costs, all of which reduce the gain as well as the cash, so we'll calculate those too
    # rent side: need to sell investments
    # First do buy case
    # Realistically you wouldn't sell all your investments at once...
    # you'd spread it out, and there's probably some optimal way to do that...
    # but here we assume all at once...
    # TODO maybe I should do it separately. After all, there may be a HUGE cap gains in one year, so doing it all at once may make it seem like buying is worse than it really is
    #
    # The sale is treated as happening in the tax year AFTER the projection ends:
    # sold the following January, the same convention as
    # RentalVsInvestExperiment._liquidate. That is why the sale's gains are taxed
    # at month num_months + 1 and stack on salary alone. The last projected
    # year's rental income, mortgage interest deduction and dividends were
    # already taxed at that year's boundary in Calculator, so adding them here
    # would tax them twice. And in a January sale year they would be zero
    # anyway: the home is sold so there is no rent, the loan is paid off so no
    # interest accrues, and the account is sold so no dividends arrive.
    #
    # The one approximation is the salary itself: that next year's is taken to
    # be the same as the last projected year's.
    annual_income = sum(
        personal_config.get_ordinary_incomes(num_years * MONTHS_PER_YEAR)[
            -1 - MONTHS_PER_YEAR : -1
        ]
    )
    # get cap gains on investments if buying
    cap_gains_from_selling_investments_if_buying = _cap_gains_from_selling_investments(
        market_balance_if_buying, investment_cost_basis_if_buying
    )
    # get cap gains on home
    # don't want to separately find tax for investments and home, since they don't contribute "proportionally"
    # due to tax bracketing. Find total cap gains, then calculate tax
    # A home lived in excludes part of its gain; one rented out excludes none.
    # Applied to the home's gain alone, before it joins the investment gains,
    # because the exclusion is a property rule and does not touch them.
    cap_gains_from_selling_home = tax_module.taxable_gain_on_a_home_sale(
        # losses are not modelled: a sale at a loss is taxed as no gain
        max(home_sale.gain, 0),
        is_a_home_you_lived_in=is_a_home_you_lived_in,
    )
    total_cap_gains_if_buying = (
        cap_gains_from_selling_investments_if_buying + cap_gains_from_selling_home
    )
    num_months = num_years * MONTHS_PER_YEAR
    cap_gains_tax_if_buying = tax_module.extra_tax_from(
        num_months + 1,
        TaxableAmounts(ordinary_income=annual_income),
        TaxableAmounts(long_term_capital_gains=total_cap_gains_if_buying),
    ).long_term_capital_gain
    wealth_if_buying = (
        -loan_balance
        + market_balance_if_buying
        + home_sale.amount_realized
        - cap_gains_tax_if_buying
    )

    # Now do rent case
    cap_gains_from_selling_investments_if_renting = _cap_gains_from_selling_investments(
        market_balance_if_renting, investment_cost_basis_if_renting
    )
    total_cap_gains_if_renting = cap_gains_from_selling_investments_if_renting
    cap_gains_tax_if_renting = tax_module.extra_tax_from(
        num_months + 1,
        TaxableAmounts(ordinary_income=annual_income),
        TaxableAmounts(long_term_capital_gains=total_cap_gains_if_renting),
    ).long_term_capital_gain
    wealth_if_renting = market_balance_if_renting - cap_gains_tax_if_renting
    return FinalState(
        wealth_if_renting=wealth_if_renting,
        wealth_if_buying=wealth_if_buying,
        tax_if_renting=cap_gains_tax_if_renting,
        tax_if_buying=cap_gains_tax_if_buying,
    )


def _run_rent_vs_buy(
    experiment_config: ExperimentConfig, experiment_writer: ExperimentWriter
) -> None:
    """Compare renting a home to live in against buying one to live in.

    Writes the initial state, the month-by-month projection, and the final
    comparison into the experiment's output directory.
    """
    num_years = experiment_config.num_years
    market_config = experiment_config.market_config
    personal_config = experiment_config.personal_config
    rent_config = experiment_config.rent_config
    buy_config = experiment_config.buy_config
    start_date = experiment_config.start_date
    tax_module = TaxModule(market_config)

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

    # Everything the sale needs, read off the projection once: each value is the
    # one at the horizon, the projection's last month.
    assert len(projection) % MONTHS_PER_YEAR == 1
    final_home_value = projection[("Buy", "Home Value")].iloc[-1]
    home_sale = compute_home_sale(
        final_sale_price=final_home_value,
        purchase_price=projection[("Buy", "Home Value")].iloc[0],
        selling_costs=buy_config.get_selling_costs(final_home_value),
        part_of_basis_upfront_one_time_cost=(
            buy_config.get_part_of_basis_upfront_one_time_cost()
        ),
    )
    final_state = _liquidate_rent_vs_buy(
        market_balance_if_renting=projection[("Rent", "Invested (Pre-Tax)")].iloc[-1],
        investment_cost_basis_if_renting=projection[
            ("Rent", "Invested Cost Basis")
        ].iloc[-1],
        market_balance_if_buying=projection[("Buy", "Invested (Pre-Tax)")].iloc[-1],
        investment_cost_basis_if_buying=projection[("Buy", "Invested Cost Basis")].iloc[
            -1
        ],
        home_sale=home_sale,
        loan_balance=projection[("Buy", "Loan Amount")].iloc[-1],
        is_a_home_you_lived_in=not buy_config.rental_income_config,
        personal_config=personal_config,
        tax_module=tax_module,
        num_years=num_years,
    )
    experiment_writer.write_xlsx_df(
        "final_state.xlsx", final_state.get_df(), num_header_rows=1
    )


def _run_rental_vs_invest(
    experiment_config: ExperimentConfig, experiment_writer: ExperimentWriter
) -> None:
    """Compare buying a property to rent out against investing the same money.

    Where you live does not appear: it is the same in both worlds, so it cancels
    out of the difference between them. That is why no rent config is read here.

    Writes the initial state, the month-by-month projection, and the final
    comparison into the experiment's output directory -- the same three files as
    the other comparison, so the two are readable side by side.
    """
    experiment = RentalVsInvestExperiment(
        experiment_config.buy_config,
        experiment_config.market_config,
        experiment_config.personal_config,
        experiment_config.num_years,
        experiment_config.start_date,
    )
    experiment_writer.write_xlsx_df(
        "initial_state.xlsx", experiment.initial_state.get_df(), num_header_rows=1
    )
    experiment_writer.write_xlsx_df(
        "projection.xlsx", experiment.get_projection_df(), num_header_rows=2
    )
    experiment_writer.write_xlsx_df(
        "final_state.xlsx", experiment.final_state.get_df(), num_header_rows=1
    )


def main() -> None:
    """Main method; entrypoint for this repo."""

    # get args; set up `--help` and `-h`
    args = _get_args()

    # load configs
    experiment_config = ExperimentConfig.parse(args.experiment_config)

    # initialize experiment writer
    experiment_writer = ExperimentWriter(args.experiment_name)
    # dump configs in output dir (to keep record of configs)
    experiment_writer.write_yaml("configs.yaml", experiment_config)

    # Dispatch on the mode explicitly rather than falling through on an else, so
    # that adding a third comparison and forgetting to wire it up fails loudly
    # instead of quietly running the wrong one.
    if experiment_config.mode == ExperimentConfig.RENT_VS_BUY:
        _run_rent_vs_buy(experiment_config, experiment_writer)
    elif experiment_config.mode == ExperimentConfig.RENTAL_VS_INVEST:
        _run_rental_vs_invest(experiment_config, experiment_writer)
    else:
        raise AssertionError(f"no runner wired up for mode {experiment_config.mode}")


if __name__ == "__main__":
    main()
