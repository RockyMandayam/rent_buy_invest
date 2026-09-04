from copy import deepcopy

import pytest

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.core.rental_vs_invest_experiment import RentalVsInvestExperiment
from rent_buy_invest.io import io_utils
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

EXPERIMENT_CONFIG_PATH = (
    "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
)
BUY_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-buy-config.yaml"
NUM_YEARS = 30


def _experiment(
    buy_config: BuyConfig = None, num_years: int = NUM_YEARS
) -> RentalVsInvestExperiment:
    experiment_config = ExperimentConfig.parse(EXPERIMENT_CONFIG_PATH)
    return RentalVsInvestExperiment(
        buy_config if buy_config is not None else experiment_config.buy_config,
        experiment_config.market_config,
        experiment_config.personal_config,
        num_years,
        experiment_config.start_date,
    )


def _profitable_buy_config() -> BuyConfig:
    """The shared fixture's rental loses money every non-December month.

    Without this, the branch where the buying world is the one with money to
    invest is only ever reached by the annual tax refund.
    """
    kwargs = deepcopy(io_utils.read_yaml(BUY_CONFIG_PATH))
    kwargs["rental_income_config"]["monthly_rental_income"] = 20_000.0
    kwargs["rental_income_config"]["occupancy_rate"] = 1.0
    kwargs["rental_income_config"]["rental_income_waiting_period_months"] = 0
    return BuyConfig(**kwargs)


def test_rejects_a_zero_length_projection() -> None:
    experiment_config = ExperimentConfig.parse(EXPERIMENT_CONFIG_PATH)
    with pytest.raises(AssertionError):
        RentalVsInvestExperiment(
            experiment_config.buy_config,
            experiment_config.market_config,
            experiment_config.personal_config,
            0,
            experiment_config.start_date,
        )


def test_projection_covers_month_zero_through_the_horizon() -> None:
    projection = _experiment().get_projection_df()
    assert projection.shape[0] == NUM_YEARS * MONTHS_PER_YEAR + 1


def test_investing_world_starts_with_what_buying_would_have_cost() -> None:
    """Buying spends the money on day one; investing puts the same amount in."""
    experiment = _experiment()
    buy_config = experiment.buy_config
    projection = experiment.get_projection_df()

    assert experiment.upfront_cost_of_buying == pytest.approx(
        buy_config.down_payment + buy_config.get_upfront_one_time_cost()
    )
    assert projection[("Invest", "Invested (Pre-Tax)")].iloc[0] == pytest.approx(
        experiment.upfront_cost_of_buying
    )
    # buying leaves you holding a property, not investments
    assert projection[("Buy Rental", "Invested (Pre-Tax)")].iloc[0] == 0


def test_tax_is_settled_once_a_year() -> None:
    projection = _experiment().get_projection_df()
    taxes = projection[("Buy Rental", "Tax")].tolist()

    for month, tax in enumerate(taxes):
        if month % MONTHS_PER_YEAR == MONTHS_PER_YEAR - 1:
            assert tax != 0, month
        else:
            assert tax == 0, month


def test_after_tax_cash_flow_is_the_property_cash_flow_less_tax() -> None:
    experiment = _experiment()
    projection = experiment.get_projection_df()
    pretax = experiment.rental_property.monthly_pretax_cash_flow

    for month in (0, 5, 11, 100, NUM_YEARS * MONTHS_PER_YEAR):
        assert projection[("Buy Rental", "Cash Flow (After Tax)")].iloc[
            month
        ] == pytest.approx(
            pretax[month] - projection[("Buy Rental", "Tax")].iloc[month]
        )


def test_surplus_is_what_owning_the_property_left_you_with() -> None:
    projection = _experiment().get_projection_df()

    assert projection[("Buy Rental", "Surplus")].tolist() == (
        projection[("Buy Rental", "Cash Flow (After Tax)")].tolist()
    )


def test_a_losing_month_grows_only_the_investing_world() -> None:
    experiment = _experiment()
    projection = experiment.get_projection_df()

    month = 5  # inside the rental income waiting period, so a loss
    surplus = projection[("Buy Rental", "Surplus")].iloc[month]
    assert surplus < 0

    buying = projection[("Buy Rental", "Invested (Pre-Tax)")]
    investing = projection[("Invest", "Invested (Pre-Tax)")]
    grow = experiment.market_config.get_pretax_monthly_wealth
    # the shortfall goes to the investing world, and buying only compounds
    assert buying.iloc[month + 1] == pytest.approx(grow(buying.iloc[month], 1)[1])
    assert investing.iloc[month + 1] == pytest.approx(
        grow(investing.iloc[month], 1)[1] - surplus
    )


def test_a_winning_month_grows_only_the_buying_world() -> None:
    experiment = _experiment(_profitable_buy_config())
    projection = experiment.get_projection_df()

    month = 5
    surplus = projection[("Buy Rental", "Surplus")].iloc[month]
    assert surplus > 0

    buying = projection[("Buy Rental", "Invested (Pre-Tax)")]
    investing = projection[("Invest", "Invested (Pre-Tax)")]
    grow = experiment.market_config.get_pretax_monthly_wealth
    assert buying.iloc[month + 1] == pytest.approx(
        grow(buying.iloc[month], 1)[1] + surplus
    )
    assert investing.iloc[month + 1] == pytest.approx(grow(investing.iloc[month], 1)[1])


def test_a_profitable_rental_owes_tax_rather_than_saving_it() -> None:
    """The shared fixture only ever reaches the loss branch of the tax."""
    projection = _experiment(_profitable_buy_config()).get_projection_df()
    first_year_end = projection[("Buy Rental", "Tax")].iloc[MONTHS_PER_YEAR - 1]

    assert first_year_end > 0


def test_equity_is_the_property_value_less_what_is_still_owed() -> None:
    experiment = _experiment()
    projection = experiment.get_projection_df()

    for month in (0, 1, 200, NUM_YEARS * MONTHS_PER_YEAR):
        assert projection[("Buy Rental", "Equity")].iloc[month] == pytest.approx(
            projection[("Buy Rental", "Property Value")].iloc[month]
            - projection[("Buy Rental", "Loan Amount")].iloc[month]
        )


def test_nothing_is_sold_before_the_horizon() -> None:
    """This projection holds the property throughout; selling is a separate step."""
    projection = _experiment().get_projection_df()

    assert projection[("Buy Rental", "Loan Amount")].iloc[-1] >= 0
    assert projection[("Buy Rental", "Equity")].iloc[-1] > 0


def _underwater_buy_config() -> BuyConfig:
    """Borrow almost everything, and let the property not appreciate.

    Selling then costs more than it brings in, which is the only way to reach a
    negative sale proceeds figure.
    """
    kwargs = deepcopy(io_utils.read_yaml(BUY_CONFIG_PATH))
    kwargs["down_payment_fraction"] = 0.01
    kwargs["annual_home_appreciation_rate"] = 0.0
    return BuyConfig(**kwargs)


def test_wealth_is_what_each_world_is_left_holding() -> None:
    final_state = _experiment().final_state

    assert final_state.wealth_if_buying == pytest.approx(
        final_state.market_balance_if_buying
        + final_state.sale_proceeds
        - final_state.tax_if_buying
    )
    # the investing world owns no property, so it has only its account
    assert final_state.wealth_if_investing == pytest.approx(
        final_state.market_balance_if_investing - final_state.tax_if_investing
    )


def test_the_buying_worlds_gains_are_taxed_together_not_separately() -> None:
    """Brackets are progressive, so splitting them would understate the tax."""
    experiment = _experiment()
    sale = experiment.rental_property.sale(
        experiment.property_values[-1], experiment.num_months
    )
    month = experiment.num_months + 1
    income = sum(
        experiment.ordinary_incomes[
            experiment.num_months - MONTHS_PER_YEAR : experiment.num_months
        ]
    )
    investment_gain = (
        experiment.final_state.market_balance_if_buying - experiment.basis_if_buying[-1]
    )

    together = experiment.tax_module.tax_on_realized_gains(
        month,
        income,
        sale.depreciation_recapture_gain,
        sale.long_term_capital_gain + investment_gain,
    ).total
    apart = (
        experiment.tax_module.tax_on_realized_gains(
            month,
            income,
            sale.depreciation_recapture_gain,
            sale.long_term_capital_gain,
        ).total
        + experiment.tax_module.tax_on_realized_gains(
            month, income, 0, investment_gain
        ).total
    )

    assert together > apart
    # the experiment used the combined figure, not the split one. At this horizon
    # the points have fully amortized, so no deduction offsets it -- the 10-year
    # case below covers that.
    assert experiment.final_state.tax_if_buying == pytest.approx(together)


def test_the_unamortized_points_reduce_the_sale_year_tax() -> None:
    experiment = _experiment(num_years=10)
    sale = experiment.rental_property.sale(
        experiment.property_values[-1], experiment.num_months
    )

    # a 30-year loan sold after 10 years still has most of its points undeducted
    assert sale.unamortized_discount_points > 0
    gains_tax = experiment.tax_module.tax_on_realized_gains(
        experiment.num_months + 1,
        sum(
            experiment.ordinary_incomes[
                experiment.num_months - MONTHS_PER_YEAR : experiment.num_months
            ]
        ),
        sale.depreciation_recapture_gain,
        sale.long_term_capital_gain
        + (
            experiment.final_state.market_balance_if_buying
            - experiment.basis_if_buying[-1]
        ),
    ).total
    assert experiment.final_state.tax_if_buying < gains_tax


def test_selling_underwater_reduces_wealth_rather_than_being_ignored() -> None:
    """Owing more than the sale brings in is money you bring to closing."""
    experiment = _experiment(_underwater_buy_config(), num_years=1)
    final_state = experiment.final_state

    assert final_state.sale_proceeds < 0
    assert final_state.wealth_if_buying == pytest.approx(
        final_state.market_balance_if_buying
        + final_state.sale_proceeds
        - final_state.tax_if_buying
    )
    assert final_state.wealth_if_buying < final_state.market_balance_if_buying


def test_a_sale_at_a_loss_owes_no_tax_on_the_property() -> None:
    experiment = _experiment(_underwater_buy_config(), num_years=1)
    sale = experiment.rental_property.sale(
        experiment.property_values[-1], experiment.num_months
    )

    assert sale.total_gain < 0
    assert sale.depreciation_recapture_gain == 0
    assert sale.long_term_capital_gain == 0


def test_market_gains_exclude_the_money_that_was_paid_in() -> None:
    """Basis is every deposit, not just the opening balance.

    A world that pays into the market monthly for thirty years is not taxed on the
    money it paid in -- only on what that money earned.
    """
    experiment = _experiment()

    deposits_if_buying = sum(s for s in experiment.buy_surpluses[:-1] if s > 0)
    deposits_if_investing = sum(-s for s in experiment.buy_surpluses[:-1] if s < 0)

    assert experiment.basis_if_buying[-1] == pytest.approx(deposits_if_buying)
    assert experiment.basis_if_investing[-1] == pytest.approx(
        experiment.upfront_cost_of_buying + deposits_if_investing
    )
    # both worlds paid in a lot, so ignoring it would overstate the gain badly
    assert deposits_if_investing > experiment.upfront_cost_of_buying


def test_market_basis_tracks_the_balance_month_by_month() -> None:
    """Basis only rises on a deposit; the balance also rises with the market."""
    experiment = _experiment()

    for lst in (experiment.basis_if_buying, experiment.basis_if_investing):
        assert len(lst) == experiment.num_months + 1
        # a cost basis never falls
        assert all(b >= a for a, b in zip(lst, lst[1:]))

    # and the balance outgrows it, because the market grew the deposits
    assert experiment.invested_if_investing[-1] > experiment.basis_if_investing[-1]


def test_a_world_taxed_on_its_deposits_would_owe_far_more() -> None:
    """Pins the size of the bug this guards against."""
    experiment = _experiment()
    final_state = experiment.final_state
    month = experiment.num_months + 1
    income = sum(
        experiment.ordinary_incomes[
            experiment.num_months - MONTHS_PER_YEAR : experiment.num_months
        ]
    )

    correct = final_state.tax_if_investing
    if_basis_ignored = experiment.tax_module.tax_on_realized_gains(
        month, income, 0, final_state.market_balance_if_investing
    ).total

    assert if_basis_ignored > correct
    assert if_basis_ignored - correct > 100_000


def test_the_points_deduction_comes_off_before_the_gains_stack() -> None:
    """A deduction lowers the income the gains stack on, not just the tax on it.

    Computing the two in parallel would put the gains too high in the brackets.
    Needs a purpose-built config: with the shared fixture the deduction never
    crosses a bracket edge, so the two orderings agree and nothing is proved.
    """
    buy_kwargs = deepcopy(io_utils.read_yaml(BUY_CONFIG_PATH))
    buy_kwargs["mortgage_discount_points_fee_fraction"] = 0.05  # the maximum allowed
    personal_kwargs = deepcopy(
        io_utils.read_yaml(
            "rent_buy_invest/core/test_resources/test-personal-config.yaml"
        )
    )
    # sits just above the top of the 0% capital gains band, so the deduction
    # pushes the gains down into it
    personal_kwargs["ordinary_income"] = 56_000.0
    personal_kwargs["ordinary_income_growth_rate"] = 0.0

    experiment_config = ExperimentConfig.parse(EXPERIMENT_CONFIG_PATH)
    experiment = RentalVsInvestExperiment(
        BuyConfig(**buy_kwargs),
        experiment_config.market_config,
        PersonalConfig(**personal_kwargs),
        10,
        experiment_config.start_date,
    )

    month = experiment.num_months
    tax_month = month + 1
    income = sum(experiment.ordinary_incomes[month - MONTHS_PER_YEAR : month])
    sale = experiment.rental_property.sale(experiment.property_values[-1], month)
    gain = max(experiment.invested_if_buying[-1] - experiment.basis_if_buying[-1], 0)
    assert sale.unamortized_discount_points > 0

    # what the gains would cost with the deduction ignored entirely
    stacked_on_full_income = experiment.tax_module.tax_on_realized_gains(
        tax_month,
        income,
        sale.depreciation_recapture_gain,
        sale.long_term_capital_gain + gain,
    ).total
    # and with it applied, which is what the experiment asks for
    sequenced = experiment.tax_module.tax_on_realized_gains(
        tax_month,
        income,
        sale.depreciation_recapture_gain,
        sale.long_term_capital_gain + gain,
        ordinary_income_deduction=sale.unamortized_discount_points,
    )

    # the deduction is worth more than its own tax saving, because it also drops
    # the gains into a lower band
    assert sequenced.tax_saved_by_deduction > 0
    assert (
        stacked_on_full_income - sequenced.total
    ) > sequenced.tax_saved_by_deduction + 1_000
    assert experiment.final_state.tax_if_buying == pytest.approx(sequenced.total)
