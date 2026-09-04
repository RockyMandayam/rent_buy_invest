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


def test_realized_gains_tax_charges_recapture_at_ordinary_rates_below_the_cap() -> None:
    tax_module = _tax_module()
    recapture = 76_384.88
    result = tax_module.tax_on_realized_gains(MONTH, 124_886, recapture, 0)

    # this config's top ordinary rate is 15% here, well under the 25% cap
    assert result.depreciation_recapture_tax == pytest.approx(0.15 * recapture)
    assert (
        result.depreciation_recapture_tax < MAX_DEPRECIATION_RECAPTURE_RATE * recapture
    )


def test_realized_gains_tax_caps_recapture_at_the_maximum_rate() -> None:
    tax_module = _high_bracket_tax_module()
    recapture = 100_000.0
    # 200,000 of salary puts every dollar of recapture in the 37% band
    result = tax_module.tax_on_realized_gains(MONTH, 200_000, recapture, 0)

    assert result.depreciation_recapture_tax == pytest.approx(
        MAX_DEPRECIATION_RECAPTURE_RATE * recapture
    )
    assert result.depreciation_recapture_tax < 0.37 * recapture


def test_realized_gains_tax_stacks_capital_gain_above_the_recapture() -> None:
    """Capital gain starts where the recapture ended, not back at ordinary income.

    Ignoring the order would understate the rate, worst in a low-income year.
    """
    tax_module = _tax_module()
    market_config = tax_module.market_config
    ordinary_income, recapture, capital_gain = 0, 76_384.88, 160_745.00

    result = tax_module.tax_on_realized_gains(
        MONTH, ordinary_income, recapture, capital_gain
    )

    unstacked = market_config.get_tax(
        MONTH, ordinary_income, long_term_capital_gains=capital_gain
    ) - market_config.get_tax(MONTH, ordinary_income)
    stacked = market_config.get_tax(
        MONTH, ordinary_income + recapture, long_term_capital_gains=capital_gain
    ) - market_config.get_tax(MONTH, ordinary_income + recapture)

    assert result.long_term_capital_gain_tax == pytest.approx(stacked)
    assert result.long_term_capital_gain_tax > unstacked


def test_realized_gains_tax_total_is_the_sum_of_its_parts() -> None:
    result = _tax_module().tax_on_realized_gains(MONTH, 124_886, 76_384.88, 160_745.00)

    # the full equation, with no deduction in play here so that term is zero
    assert result.tax_saved_by_deduction == 0
    assert result.total == pytest.approx(
        result.depreciation_recapture_tax
        + result.long_term_capital_gain_tax
        - result.tax_saved_by_deduction
    )
    assert result.total > 0


def test_realized_gains_tax_on_a_sale_with_no_gain_is_zero() -> None:
    """A sale at a loss arrives here as two zeros, so nothing is owed."""
    result = _tax_module().tax_on_realized_gains(MONTH, 124_886, 0, 0)

    assert result.depreciation_recapture_tax == 0
    assert result.long_term_capital_gain_tax == 0
    assert result.total == 0


def test_realized_gains_tax_rejects_negative_amounts() -> None:
    tax_module = _tax_module()
    with pytest.raises(AssertionError):
        tax_module.tax_on_realized_gains(MONTH, -1, 100, 100)
    with pytest.raises(AssertionError):
        tax_module.tax_on_realized_gains(MONTH, 100, -1, 100)
    with pytest.raises(AssertionError):
        tax_module.tax_on_realized_gains(MONTH, 100, 100, -1)
    with pytest.raises(AssertionError):
        tax_module.tax_on_realized_gains(-1, 100, 100, 100)


def test_tax_saved_by_deduction_returns_a_positive_saving() -> None:
    """A saving is positive, so a caller subtracts it rather than adding."""
    tax_module = _tax_module()
    saved = tax_module.tax_saved_by_deduction(MONTH, 124_886, 10_000)

    # 124,886 of salary sits in the 15% band, so deducting 10,000 saves 1,500
    assert saved == pytest.approx(1_500)
    assert saved > 0
    # the same figure the loss branch reports, with the opposite sign
    assert saved == pytest.approx(
        -tax_module.annual_rental_activity_tax(MONTH, 124_886, -10_000)
    )


def test_tax_saved_by_deduction_cannot_exceed_the_income_it_offsets() -> None:
    tax_module = _tax_module()

    assert tax_module.tax_saved_by_deduction(MONTH, 0, 10_000) == 0
    # deducting more than you earned saves only what the income was worth
    all_of_it = tax_module.tax_saved_by_deduction(MONTH, 100_000, 100_000)
    more_than_all = tax_module.tax_saved_by_deduction(MONTH, 100_000, 500_000)
    assert more_than_all == pytest.approx(all_of_it)


def test_tax_saved_by_deduction_rejects_negative_amounts() -> None:
    tax_module = _tax_module()
    with pytest.raises(AssertionError):
        tax_module.tax_saved_by_deduction(MONTH, -1, 100)
    with pytest.raises(AssertionError):
        tax_module.tax_saved_by_deduction(MONTH, 100, -1)
    with pytest.raises(AssertionError):
        tax_module.tax_saved_by_deduction(-1, 100, 100)


def test_realized_gains_tax_applies_a_deduction_before_the_gains_stack() -> None:
    """A deduction saves ordinary-rate tax and lowers what the gains stack on."""
    tax_module = _tax_module()
    income, recapture, capital_gain, deduction = 60_000, 20_000, 100_000, 20_000

    without = tax_module.tax_on_realized_gains(MONTH, income, recapture, capital_gain)
    with_deduction = tax_module.tax_on_realized_gains(
        MONTH, income, recapture, capital_gain, ordinary_income_deduction=deduction
    )

    assert without.tax_saved_by_deduction == 0
    assert with_deduction.tax_saved_by_deduction > 0
    # the total falls by more than the ordinary-rate saving alone, because the
    # gains also moved down the brackets
    assert without.total - with_deduction.total > with_deduction.tax_saved_by_deduction
    assert with_deduction.total == pytest.approx(
        with_deduction.depreciation_recapture_tax
        + with_deduction.long_term_capital_gain_tax
        - with_deduction.tax_saved_by_deduction
    )


def test_realized_gains_tax_rejects_a_negative_deduction() -> None:
    with pytest.raises(AssertionError):
        _tax_module().tax_on_realized_gains(
            MONTH, 100, 100, 100, ordinary_income_deduction=-1
        )
