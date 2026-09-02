from copy import deepcopy

import pytest

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.core.rental_vs_invest_calculator import RentalVsInvestCalculator
from rent_buy_invest.io import io_utils
from rent_buy_invest.utils.math_utils import MONTHS_PER_YEAR

EXPERIMENT_CONFIG_PATH = (
    "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
)
BUY_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-buy-config.yaml"
NUM_YEARS = 30


def _calculator(buy_config: BuyConfig = None) -> RentalVsInvestCalculator:
    experiment_config = ExperimentConfig.parse(EXPERIMENT_CONFIG_PATH)
    return RentalVsInvestCalculator(
        buy_config if buy_config is not None else experiment_config.buy_config,
        experiment_config.market_config,
        experiment_config.personal_config,
        NUM_YEARS,
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
        RentalVsInvestCalculator(
            experiment_config.buy_config,
            experiment_config.market_config,
            experiment_config.personal_config,
            0,
            experiment_config.start_date,
        )


def test_projection_covers_month_zero_through_the_horizon() -> None:
    projection = _calculator().calculate()
    assert projection.shape[0] == NUM_YEARS * MONTHS_PER_YEAR + 1


def test_investing_world_starts_with_what_buying_would_have_cost() -> None:
    """Buying spends the money on day one; investing puts the same amount in."""
    calculator = _calculator()
    buy_config = calculator.buy_config
    projection = calculator.calculate()

    assert calculator.upfront_cost_of_buying == pytest.approx(
        buy_config.down_payment + buy_config.get_upfront_one_time_cost()
    )
    assert projection[("Invest", "Invested (Pre-Tax)")].iloc[0] == pytest.approx(
        calculator.upfront_cost_of_buying
    )
    # buying leaves you holding a property, not investments
    assert projection[("Buy Rental", "Invested (Pre-Tax)")].iloc[0] == 0


def test_tax_is_settled_once_a_year() -> None:
    projection = _calculator().calculate()
    taxes = projection[("Buy Rental", "Tax")].tolist()

    for month, tax in enumerate(taxes):
        if month % MONTHS_PER_YEAR == MONTHS_PER_YEAR - 1:
            assert tax != 0, month
        else:
            assert tax == 0, month


def test_after_tax_cash_flow_is_the_property_cash_flow_less_tax() -> None:
    calculator = _calculator()
    projection = calculator.calculate()
    pretax = calculator.rental_property.monthly_pretax_cash_flow

    for month in (0, 5, 11, 100, NUM_YEARS * MONTHS_PER_YEAR):
        assert projection[("Buy Rental", "Cash Flow (After Tax)")].iloc[
            month
        ] == pytest.approx(
            pretax[month] - projection[("Buy Rental", "Tax")].iloc[month]
        )


def test_surplus_is_what_owning_the_property_left_you_with() -> None:
    projection = _calculator().calculate()

    assert projection[("Buy Rental", "Surplus")].tolist() == (
        projection[("Buy Rental", "Cash Flow (After Tax)")].tolist()
    )


def test_a_losing_month_grows_only_the_investing_world() -> None:
    calculator = _calculator()
    projection = calculator.calculate()

    month = 5  # inside the rental income waiting period, so a loss
    surplus = projection[("Buy Rental", "Surplus")].iloc[month]
    assert surplus < 0

    buying = projection[("Buy Rental", "Invested (Pre-Tax)")]
    investing = projection[("Invest", "Invested (Pre-Tax)")]
    grow = calculator.market_config.get_pretax_monthly_wealth
    # the shortfall goes to the investing world, and buying only compounds
    assert buying.iloc[month + 1] == pytest.approx(grow(buying.iloc[month], 1)[1])
    assert investing.iloc[month + 1] == pytest.approx(
        grow(investing.iloc[month], 1)[1] - surplus
    )


def test_a_winning_month_grows_only_the_buying_world() -> None:
    calculator = _calculator(_profitable_buy_config())
    projection = calculator.calculate()

    month = 5
    surplus = projection[("Buy Rental", "Surplus")].iloc[month]
    assert surplus > 0

    buying = projection[("Buy Rental", "Invested (Pre-Tax)")]
    investing = projection[("Invest", "Invested (Pre-Tax)")]
    grow = calculator.market_config.get_pretax_monthly_wealth
    assert buying.iloc[month + 1] == pytest.approx(
        grow(buying.iloc[month], 1)[1] + surplus
    )
    assert investing.iloc[month + 1] == pytest.approx(grow(investing.iloc[month], 1)[1])


def test_a_profitable_rental_owes_tax_rather_than_saving_it() -> None:
    """The shared fixture only ever reaches the loss branch of the tax."""
    projection = _calculator(_profitable_buy_config()).calculate()
    first_year_end = projection[("Buy Rental", "Tax")].iloc[MONTHS_PER_YEAR - 1]

    assert first_year_end > 0


def test_equity_is_the_property_value_less_what_is_still_owed() -> None:
    calculator = _calculator()
    projection = calculator.calculate()

    for month in (0, 1, 200, NUM_YEARS * MONTHS_PER_YEAR):
        assert projection[("Buy Rental", "Equity")].iloc[month] == pytest.approx(
            projection[("Buy Rental", "Property Value")].iloc[month]
            - projection[("Buy Rental", "Loan Amount")].iloc[month]
        )


def test_nothing_is_sold_before_the_horizon() -> None:
    """This projection holds the property throughout; selling is a separate step."""
    projection = _calculator().calculate()

    assert projection[("Buy Rental", "Loan Amount")].iloc[-1] >= 0
    assert projection[("Buy Rental", "Equity")].iloc[-1] > 0
