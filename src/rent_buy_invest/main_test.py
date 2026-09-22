import sys

import pytest

from rent_buy_invest.configs.experiment_config import ExperimentConfig
from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.configs.personal_config import PersonalConfig
from rent_buy_invest.core.home_sale import HomeSale
from rent_buy_invest.core.tax import TaxModule
from rent_buy_invest.main import (
    _cap_gains_from_selling_investments,
    _get_args,
    _liquidate_rent_vs_buy,
    _run_rent_vs_buy,
)

# Brackets round enough that every expected tax below can be worked out by hand:
# no tax on the first 100,000 of income, 20% on long-term capital gains above it,
# and no inflation, so the brackets do not move over the projection.
HAND_CHECKABLE_TAX_MODULE = TaxModule(
    MarketConfig(
        market_rate_of_return=0.07,
        market_dividend_yield=0.0,
        tax_brackets_inflation=0.0,
        annual_inflation_rate=0.0,
        tax_brackets={
            "ordinary_income_tax_brackets": [
                {"upper_limit": 100_000.0, "tax_rate": 0.0},
                {"upper_limit": float("inf"), "tax_rate": 0.3},
            ],
            "long_term_capital_gains_tax_brackets": [
                {"upper_limit": 100_000.0, "tax_rate": 0.0},
                {"upper_limit": float("inf"), "tax_rate": 0.2},
            ],
        },
    )
)
# A flat 36,000 salary fills the first 36,000 of the 0% band, so a sale's gains
# are untaxed for their first 64,000 and taxed at 20% from there. It is 3,000 a
# month exactly: monthly income is rounded to the cent, so a salary that does not
# divide into whole cents would not add back up to itself.
SALARY = 36_000.0
PERSONAL_CONFIG = PersonalConfig(
    ordinary_income=SALARY, ordinary_income_growth_rate=0.0, years_till_retirement=50
)
NUM_YEARS = 2


def _liquidate(**overrides):
    """Liquidate with nothing to sell but what a test puts in ``overrides``.

    By default both market accounts are all basis and the home breaks even, so
    every gain -- and so every dollar of tax -- comes from the test itself.
    """
    kwargs = dict(
        market_balance_if_renting=0.0,
        investment_cost_basis_if_renting=0.0,
        market_balance_if_buying=0.0,
        investment_cost_basis_if_buying=0.0,
        home_sale=HomeSale(amount_realized=500_000.0, cost_basis=500_000.0),
        loan_balance=0.0,
        is_a_home_you_lived_in=True,
        personal_config=PERSONAL_CONFIG,
        tax_module=HAND_CHECKABLE_TAX_MODULE,
        num_years=NUM_YEARS,
    )
    kwargs.update(overrides)
    return _liquidate_rent_vs_buy(**kwargs)


def test_cap_gains_from_selling_investments_is_the_balance_less_the_basis() -> None:
    """Only what the money earned is gain; what was paid in is not."""
    assert _cap_gains_from_selling_investments(1500, 1300) == pytest.approx(200)


def test_cap_gains_from_selling_investments_reports_a_loss_as_no_gain() -> None:
    """TODO: losses are floored rather than deducted; see the helper's docstring."""
    assert _cap_gains_from_selling_investments(700, 1000) == 0


def test_cap_gains_from_selling_investments_never_taxes_a_balance_of_all_basis() -> (
    None
):
    """A flat market that only received deposits, or dividends already taxed."""
    assert _cap_gains_from_selling_investments(300, 300) == 0


def test_liquidate_rent_vs_buy_taxes_the_renting_worlds_market_gain() -> None:
    final_state = _liquidate(
        market_balance_if_renting=500_000.0,
        investment_cost_basis_if_renting=300_000.0,
    )

    # 200,000 of gain: the first 64,000 untaxed, 136,000 at 20%
    assert final_state.tax_if_renting == pytest.approx(27_200)
    assert final_state.wealth_if_renting == pytest.approx(500_000 - 27_200)


def test_liquidate_rent_vs_buy_pays_off_the_loan_from_the_sale() -> None:
    final_state = _liquidate(
        market_balance_if_buying=10_000.0,
        investment_cost_basis_if_buying=10_000.0,
        loan_balance=150_000.0,
    )

    # the home broke even and the account is all basis, so nothing is taxed
    assert final_state.tax_if_buying == 0
    assert final_state.wealth_if_buying == pytest.approx(10_000 + 500_000 - 150_000)


def test_liquidate_rent_vs_buy_does_not_tax_a_home_sold_at_a_loss() -> None:
    """A loss on the home is taxed as no gain, and never offsets other gains.

    Losses are not modelled. The floor that enforces that once had no test at
    all: it could be deleted and the whole suite still passed.
    """
    final_state = _liquidate(
        market_balance_if_buying=260_000.0,
        investment_cost_basis_if_buying=100_000.0,
        home_sale=HomeSale(amount_realized=400_000.0, cost_basis=500_000.0),
        is_a_home_you_lived_in=False,
    )

    # only the market account's 160,000 is taxed: 96,000 of it at 20%. The
    # home's 100,000 loss does not bring that down.
    assert final_state.tax_if_buying == pytest.approx(19_200)


def test_liquidate_rent_vs_buy_excludes_part_of_the_gain_on_a_home_you_lived_in() -> (
    None
):
    final_state = _liquidate(
        home_sale=HomeSale(amount_realized=850_000.0, cost_basis=500_000.0),
        is_a_home_you_lived_in=True,
    )

    # 350,000 of gain, 250,000 of it excluded: 100,000 taxable, 36,000 at 20%
    assert final_state.tax_if_buying == pytest.approx(7_200)


def test_liquidate_rent_vs_buy_excludes_nothing_on_a_home_with_rental_income() -> None:
    final_state = _liquidate(
        home_sale=HomeSale(amount_realized=850_000.0, cost_basis=500_000.0),
        is_a_home_you_lived_in=False,
    )

    # all 350,000 taxable: 286,000 at 20%
    assert final_state.tax_if_buying == pytest.approx(57_200)


def test_liquidate_rent_vs_buy_taxes_the_buying_worlds_two_gains_together() -> None:
    """The home's gain and the market account's are one year's gains.

    Taxed separately, each would get its own untaxed 64,000, and the bill would
    come out at 14,400 instead of 27,200.
    """
    final_state = _liquidate(
        market_balance_if_buying=200_000.0,
        investment_cost_basis_if_buying=100_000.0,
        home_sale=HomeSale(amount_realized=600_000.0, cost_basis=500_000.0),
        is_a_home_you_lived_in=False,
    )

    # 200,000 of gain in all: 136,000 at 20%
    assert final_state.tax_if_buying == pytest.approx(27_200)


class _RecordingWriter:
    """Stands in for ExperimentWriter, keeping each table instead of writing it."""

    def __init__(self) -> None:
        self.dfs = {}

    def write_xlsx_df(self, name, df, num_header_rows=1) -> None:
        self.dfs[name] = df


def test_run_rent_vs_buy_liquidates_each_world_from_its_own_columns() -> None:
    """The glue between the projection and the sale, end to end.

    Every test above hands the sale its numbers directly, so none of them would
    notice ``_run_rent_vs_buy`` reading the wrong world's column. Here the whole
    run is compared against a sale fed from columns picked out independently.
    """
    experiment_config = ExperimentConfig.parse(
        "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
    )
    writer = _RecordingWriter()
    _run_rent_vs_buy(experiment_config, writer)
    projection = writer.dfs["projection.xlsx"]
    written = writer.dfs["final_state.xlsx"]

    def at_horizon(world: str, column: str) -> float:
        return projection[world][column].iloc[-1]

    buy_config = experiment_config.buy_config
    final_home_value = at_horizon("Buy", "Home Value")
    expected = _liquidate_rent_vs_buy(
        market_balance_if_renting=at_horizon("Rent", "Invested (Pre-Tax)"),
        investment_cost_basis_if_renting=at_horizon("Rent", "Invested Cost Basis"),
        market_balance_if_buying=at_horizon("Buy", "Invested (Pre-Tax)"),
        investment_cost_basis_if_buying=at_horizon("Buy", "Invested Cost Basis"),
        home_sale=HomeSale(
            amount_realized=(
                final_home_value - buy_config.get_selling_costs(final_home_value)
            ),
            cost_basis=(
                buy_config.purchase_price
                + buy_config.get_part_of_basis_upfront_one_time_cost()
            ),
        ),
        loan_balance=at_horizon("Buy", "Loan Amount"),
        # the shared test config's home has rental income
        is_a_home_you_lived_in=False,
        personal_config=experiment_config.personal_config,
        tax_module=TaxModule(experiment_config.market_config),
        num_years=experiment_config.num_years,
    )

    # the two worlds must differ, or a swap between them would go unnoticed
    assert expected.wealth_if_renting != pytest.approx(expected.wealth_if_buying)
    assert written["Rent"]["Wealth"] == pytest.approx(expected.wealth_if_renting)
    assert written["Buy"]["Wealth"] == pytest.approx(expected.wealth_if_buying)


@pytest.mark.parametrize("extension", [".yaml", ".yml"])
def test_get_args_accepts_both_yaml_extensions(monkeypatch, extension: str) -> None:
    """Both spellings are accepted.

    The ``.yml`` check once read ``args.experiment.config_endswith`` -- an attribute
    that does not exist -- so every ``.yml`` config crashed with an
    ``AttributeError``. The examples all end in ``.yaml``, which is checked first,
    so nothing exercised the broken half.
    """
    path = f"rent_buy_invest/configs/experiment-config{extension}"
    monkeypatch.setattr(sys, "argv", ["rent_buy_invest", path])

    assert _get_args().experiment_config == path


def test_get_args_rejects_other_extensions(monkeypatch) -> None:
    monkeypatch.setattr(
        sys, "argv", ["rent_buy_invest", "rent_buy_invest/configs/config.json"]
    )

    with pytest.raises(AssertionError):
        _get_args()
