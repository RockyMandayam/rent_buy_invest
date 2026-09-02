import pytest

from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.tax import MAX_DEPRECIATION_RECAPTURE_RATE, TaxModule

MARKET_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-market-config.yaml"
MONTH = 120


def _tax_module() -> TaxModule:
    return TaxModule(MarketConfig.parse(MARKET_CONFIG_PATH))


def _high_bracket_tax_module() -> TaxModule:
    """Ordinary rates above the recapture cap.

    The shared test config tops out at 20% ordinary, below the 25% cap, so it can
    never exercise the cap at all.
    """
    return TaxModule(
        MarketConfig(
            market_rate_of_return=0.07,
            tax_brackets_inflation=0.0,
            annual_inflation_rate=0.0,
            tax_brackets={
                "ordinary_income_tax_brackets": [
                    {"upper_limit": 50_000.0, "tax_rate": 0.10},
                    {"upper_limit": float("inf"), "tax_rate": 0.37},
                ],
                "long_term_capital_gains_tax_brackets": [
                    {"upper_limit": 50_000.0, "tax_rate": 0.0},
                    {"upper_limit": float("inf"), "tax_rate": 0.20},
                ],
            },
        )
    )


def test_annual_rental_activity_tax_adds_to_what_you_already_earn() -> None:
    tax_module = _tax_module()
    # the method returns only the EXTRA tax the rental causes, not the whole
    # bill: 124,886 of salary sits in the 15% band, so the next 10,000 of
    # rental income is taxed at 15% -> 1,500
    assert tax_module.annual_rental_activity_tax(
        MONTH, 124_886, 10_000
    ) == pytest.approx(1_500)


def test_annual_rental_activity_tax_returns_a_negative_for_a_loss() -> None:
    """A loss comes off other income and saves tax at the same marginal rate."""
    tax_module = _tax_module()
    owed = tax_module.annual_rental_activity_tax(MONTH, 124_886, 10_000)
    saved = tax_module.annual_rental_activity_tax(MONTH, 124_886, -10_000)

    assert saved == pytest.approx(-owed)
    assert saved < 0


def test_annual_rental_activity_tax_is_worth_nothing_without_income() -> None:
    """The documented limitation: a loss can only offset income you have."""
    tax_module = _tax_module()
    result = tax_module.annual_rental_activity_tax(MONTH, 0, -10_000)

    assert result == 0
    # and not -0.0, which would read as a bug in any output
    assert str(result) == "0.0"


def test_annual_rental_activity_tax_of_zero_costs_nothing() -> None:
    assert _tax_module().annual_rental_activity_tax(MONTH, 124_886, 0) == 0


def test_annual_rental_activity_tax_rejects_negative_income() -> None:
    with pytest.raises(AssertionError):
        _tax_module().annual_rental_activity_tax(MONTH, -1, 1_000)
    with pytest.raises(AssertionError):
        _tax_module().annual_rental_activity_tax(-1, 100, 1_000)


def test_liquidation_tax_charges_recapture_at_ordinary_rates_below_the_cap() -> None:
    tax_module = _tax_module()
    recapture = 76_384.88
    result = tax_module.liquidation_tax(MONTH, 124_886, recapture, 0)

    # this config's top ordinary rate is 15% here, well under the 25% cap
    assert result.depreciation_recapture_tax == pytest.approx(0.15 * recapture)
    assert (
        result.depreciation_recapture_tax < MAX_DEPRECIATION_RECAPTURE_RATE * recapture
    )


def test_liquidation_tax_caps_recapture_at_the_maximum_rate() -> None:
    tax_module = _high_bracket_tax_module()
    recapture = 100_000.0
    # 200,000 of salary puts every dollar of recapture in the 37% band
    result = tax_module.liquidation_tax(MONTH, 200_000, recapture, 0)

    assert result.depreciation_recapture_tax == pytest.approx(
        MAX_DEPRECIATION_RECAPTURE_RATE * recapture
    )
    assert result.depreciation_recapture_tax < 0.37 * recapture


def test_liquidation_tax_stacks_capital_gain_above_the_recapture() -> None:
    """Capital gain starts where the recapture ended, not back at ordinary income.

    Ignoring the order would understate the rate, worst in a low-income year.
    """
    tax_module = _tax_module()
    market_config = tax_module.market_config
    ordinary_income, recapture, capital_gain = 0, 76_384.88, 160_745.00

    result = tax_module.liquidation_tax(MONTH, ordinary_income, recapture, capital_gain)

    unstacked = market_config.get_tax(
        MONTH, ordinary_income, long_term_capital_gains=capital_gain
    ) - market_config.get_tax(MONTH, ordinary_income)
    stacked = market_config.get_tax(
        MONTH, ordinary_income + recapture, long_term_capital_gains=capital_gain
    ) - market_config.get_tax(MONTH, ordinary_income + recapture)

    assert result.long_term_capital_gain_tax == pytest.approx(stacked)
    assert result.long_term_capital_gain_tax > unstacked


def test_liquidation_tax_total_is_the_sum_of_its_parts() -> None:
    result = _tax_module().liquidation_tax(MONTH, 124_886, 76_384.88, 160_745.00)

    assert result.total == pytest.approx(
        result.depreciation_recapture_tax + result.long_term_capital_gain_tax
    )
    assert result.total > 0


def test_liquidation_tax_on_a_sale_with_no_gain_is_zero() -> None:
    """A sale at a loss arrives here as two zeros, so nothing is owed."""
    result = _tax_module().liquidation_tax(MONTH, 124_886, 0, 0)

    assert result.depreciation_recapture_tax == 0
    assert result.long_term_capital_gain_tax == 0
    assert result.total == 0


def test_liquidation_tax_rejects_negative_amounts() -> None:
    tax_module = _tax_module()
    with pytest.raises(AssertionError):
        tax_module.liquidation_tax(MONTH, -1, 100, 100)
    with pytest.raises(AssertionError):
        tax_module.liquidation_tax(MONTH, 100, -1, 100)
    with pytest.raises(AssertionError):
        tax_module.liquidation_tax(MONTH, 100, 100, -1)
    with pytest.raises(AssertionError):
        tax_module.liquidation_tax(-1, 100, 100, 100)
