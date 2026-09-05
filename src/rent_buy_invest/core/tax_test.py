import pytest

from rent_buy_invest.configs.market_config import MarketConfig
from rent_buy_invest.core.tax import (
    MAX_DEPRECIATION_RECAPTURE_RATE,
    TaxableAmounts,
    TaxModule,
)

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
            market_dividend_yield=0.0,
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


def test_extra_tax_from_parts_add_up_to_the_total() -> None:
    """The categories are steps of one calculation, so they cannot fail to sum."""
    tax_module = _high_bracket_tax_module()
    salary = TaxableAmounts(ordinary_income=90_000.0)

    for added in (
        TaxableAmounts(),
        TaxableAmounts(ordinary_income=20_000.0),
        TaxableAmounts(ordinary_deductions=30_000.0),
        TaxableAmounts(depreciation_recapture=40_000.0),
        TaxableAmounts(long_term_capital_gains=60_000.0),
        TaxableAmounts(
            ordinary_income=15_000.0,
            ordinary_deductions=50_000.0,
            depreciation_recapture=40_000.0,
            long_term_capital_gains=60_000.0,
        ),
    ):
        cost = tax_module.extra_tax_from(MONTH, salary, added)
        assert cost.total == pytest.approx(
            cost.ordinary + cost.depreciation_recapture + cost.long_term_capital_gain,
            abs=0.01,
        )


def test_extra_tax_from_charges_each_category_where_it_lands() -> None:
    """A category is priced on top of the ones beneath it, not from the base.

    The same capital gain costs more when there is ordinary income and recapture
    underneath it, because it starts further up the schedule.
    """
    tax_module = _high_bracket_tax_module()
    salary = TaxableAmounts(ordinary_income=20_000.0)
    gain = TaxableAmounts(long_term_capital_gains=60_000.0)

    alone = tax_module.extra_tax_from(MONTH, salary, gain)
    with_more_underneath = tax_module.extra_tax_from(
        MONTH,
        salary,
        gain + TaxableAmounts(ordinary_income=40_000.0),
    )
    assert with_more_underneath.long_term_capital_gain > alone.long_term_capital_gain

    # and a deduction pushes it back down, for the same reason
    with_a_deduction = tax_module.extra_tax_from(
        MONTH, salary, gain + TaxableAmounts(ordinary_deductions=15_000.0)
    )
    assert with_a_deduction.long_term_capital_gain < alone.long_term_capital_gain


def test_extra_tax_from_never_charges_the_base() -> None:
    """``already`` says where things land; its own tax is not the caller's bill."""
    tax_module = _high_bracket_tax_module()
    nothing_added = tax_module.extra_tax_from(
        MONTH, TaxableAmounts(ordinary_income=250_000.0), TaxableAmounts()
    )
    assert nothing_added.total == 0


def test_extra_tax_from_rental_adds_to_what_you_already_earn() -> None:
    tax_module = _tax_module()
    # only the EXTRA tax the rental causes, not the whole bill: 124,886 of salary
    # sits in the 15% band, so the next 10,000 of rental income is taxed at 15%
    cost = tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=124_886),
        TaxableAmounts(ordinary_income=10_000),
    )
    assert cost.ordinary == pytest.approx(1_500)


def test_extra_tax_from_rental_returns_a_negative_for_a_loss() -> None:
    """A loss comes off other income and saves tax at the same marginal rate."""
    tax_module = _tax_module()
    salary = TaxableAmounts(ordinary_income=124_886)
    owed = tax_module.extra_tax_from(
        MONTH, salary, TaxableAmounts(ordinary_income=10_000)
    ).ordinary
    saved = tax_module.extra_tax_from(
        MONTH, salary, TaxableAmounts(ordinary_deductions=10_000)
    ).ordinary

    assert saved == pytest.approx(-owed)
    assert saved < 0


def test_extra_tax_from_rental_is_worth_nothing_without_income() -> None:
    """The documented limitation: a loss can only offset income you have."""
    result = (
        _tax_module()
        .extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=0),
            TaxableAmounts(ordinary_deductions=10_000),
        )
        .ordinary
    )

    assert result == 0
    # and not -0.0, which would read as a bug in any output
    assert str(result) == "0.0"


def test_extra_tax_from_rental_of_zero_costs_nothing() -> None:
    assert (
        _tax_module()
        .extra_tax_from(
            MONTH, TaxableAmounts(ordinary_income=124_886), TaxableAmounts()
        )
        .ordinary
        == 0
    )


def test_extra_tax_from_rental_rejects_negative_income() -> None:
    rental_income = TaxableAmounts(ordinary_income=1_000)
    with pytest.raises(AssertionError):
        _tax_module().extra_tax_from(
            MONTH, TaxableAmounts(ordinary_income=-1), rental_income
        )
    with pytest.raises(AssertionError):
        _tax_module().extra_tax_from(
            -1, TaxableAmounts(ordinary_income=100), rental_income
        )


def test_extra_tax_from_charges_recapture_at_ordinary_rates_below_the_cap() -> None:
    tax_module = _tax_module()
    recapture = 76_384.88
    result = tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=124_886),
        TaxableAmounts(
            depreciation_recapture=recapture,
            long_term_capital_gains=0,
        ),
    )

    # this config's top ordinary rate is 15% here, well under the 25% cap
    assert result.depreciation_recapture == pytest.approx(0.15 * recapture)
    assert result.depreciation_recapture < MAX_DEPRECIATION_RECAPTURE_RATE * recapture


def test_extra_tax_from_caps_recapture_at_the_maximum_rate() -> None:
    tax_module = _high_bracket_tax_module()
    recapture = 100_000.0
    # 200,000 of salary puts every dollar of recapture in the 37% band
    result = tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=200_000),
        TaxableAmounts(depreciation_recapture=recapture),
    )

    assert result.depreciation_recapture == pytest.approx(
        MAX_DEPRECIATION_RECAPTURE_RATE * recapture
    )
    assert result.depreciation_recapture < 0.37 * recapture


def test_extra_tax_from_stacks_capital_gain_above_the_recapture() -> None:
    """Capital gain starts where the recapture ended, not back at ordinary income.

    Ignoring the order would understate the rate, worst in a low-income year.
    """
    tax_module = _tax_module()
    market_config = tax_module.market_config
    ordinary_income, recapture, capital_gain = 0, 76_384.88, 160_745.00

    result = tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=ordinary_income),
        TaxableAmounts(
            depreciation_recapture=recapture,
            long_term_capital_gains=capital_gain,
        ),
    )

    unstacked = market_config.get_tax(
        MONTH, ordinary_income, long_term_capital_gains=capital_gain
    ) - market_config.get_tax(MONTH, ordinary_income)
    stacked = market_config.get_tax(
        MONTH, ordinary_income + recapture, long_term_capital_gains=capital_gain
    ) - market_config.get_tax(MONTH, ordinary_income + recapture)

    assert result.long_term_capital_gain == pytest.approx(stacked)
    assert result.long_term_capital_gain > unstacked


def test_extra_tax_from_total_is_the_sum_of_its_parts() -> None:
    result = _tax_module().extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=124_886),
        TaxableAmounts(
            depreciation_recapture=76_384.88,
            long_term_capital_gains=160_745.00,
        ),
    )

    # the full equation, with no deduction in play here so that term is zero
    assert result.ordinary == 0
    assert result.total == pytest.approx(
        result.ordinary + result.depreciation_recapture + result.long_term_capital_gain
    )
    assert result.total > 0


def test_extra_tax_from_on_a_sale_with_no_gain_is_zero() -> None:
    """A sale at a loss arrives here as two zeros, so nothing is owed."""
    result = _tax_module().extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=124_886),
        TaxableAmounts(
            depreciation_recapture=0,
            long_term_capital_gains=0,
        ),
    )

    assert result.depreciation_recapture == 0
    assert result.long_term_capital_gain == 0
    assert result.total == 0


def test_extra_tax_from_rejects_negative_amounts() -> None:
    tax_module = _tax_module()
    with pytest.raises(AssertionError):
        tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=-1),
            TaxableAmounts(
                depreciation_recapture=100,
                long_term_capital_gains=100,
            ),
        )
    with pytest.raises(AssertionError):
        tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=100),
            TaxableAmounts(
                depreciation_recapture=-1,
                long_term_capital_gains=100,
            ),
        )
    with pytest.raises(AssertionError):
        tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=100),
            TaxableAmounts(
                depreciation_recapture=100,
                long_term_capital_gains=-1,
            ),
        )
    with pytest.raises(AssertionError):
        tax_module.extra_tax_from(
            -1,
            TaxableAmounts(ordinary_income=100),
            TaxableAmounts(
                depreciation_recapture=100,
                long_term_capital_gains=100,
            ),
        )


def test_extra_tax_from_deduction_returns_a_positive_saving() -> None:
    """A saving is positive, so a caller subtracts it rather than adding."""
    tax_module = _tax_module()
    saved = -tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=124_886),
        TaxableAmounts(
            ordinary_deductions=10_000,
        ),
    ).ordinary

    # 124,886 of salary sits in the 15% band, so deducting 10,000 saves 1,500
    assert saved == pytest.approx(1_500)
    assert saved > 0
    # the same figure the loss branch reports, with the opposite sign
    assert saved == pytest.approx(
        -tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=124_886),
            TaxableAmounts(ordinary_deductions=10_000),
        ).ordinary
    )


def test_extra_tax_from_deduction_cannot_exceed_the_income_it_offsets() -> None:
    tax_module = _tax_module()

    assert (
        -tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=0),
            TaxableAmounts(
                ordinary_deductions=10_000,
            ),
        ).ordinary
        == 0
    )
    # deducting more than you earned saves only what the income was worth
    all_of_it = -tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=100_000),
        TaxableAmounts(
            ordinary_deductions=100_000,
        ),
    ).ordinary
    more_than_all = -tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=100_000),
        TaxableAmounts(
            ordinary_deductions=500_000,
        ),
    ).ordinary
    assert more_than_all == pytest.approx(all_of_it)


def test_extra_tax_from_deduction_rejects_negative_amounts() -> None:
    tax_module = _tax_module()
    with pytest.raises(AssertionError):
        -tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=-1),
            TaxableAmounts(
                ordinary_deductions=100,
            ),
        ).ordinary
    with pytest.raises(AssertionError):
        -tax_module.extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=100),
            TaxableAmounts(
                ordinary_deductions=-1,
            ),
        ).ordinary
    with pytest.raises(AssertionError):
        -tax_module.extra_tax_from(
            -1,
            TaxableAmounts(ordinary_income=100),
            TaxableAmounts(
                ordinary_deductions=100,
            ),
        ).ordinary


def test_extra_tax_from_applies_a_deduction_before_the_gains_stack() -> None:
    """A deduction saves ordinary-rate tax and lowers what the gains stack on."""
    tax_module = _tax_module()
    income, recapture, capital_gain, deduction = 60_000, 20_000, 100_000, 20_000

    without = tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=income),
        TaxableAmounts(
            depreciation_recapture=recapture,
            long_term_capital_gains=capital_gain,
        ),
    )
    with_deduction = tax_module.extra_tax_from(
        MONTH,
        TaxableAmounts(ordinary_income=income),
        TaxableAmounts(
            ordinary_deductions=deduction,
            depreciation_recapture=recapture,
            long_term_capital_gains=capital_gain,
        ),
    )

    assert -without.ordinary == 0
    assert -with_deduction.ordinary > 0
    # the total falls by more than the ordinary-rate saving alone, because the
    # gains also moved down the brackets
    assert without.total - with_deduction.total > -with_deduction.ordinary
    assert with_deduction.total == pytest.approx(
        with_deduction.depreciation_recapture
        + with_deduction.long_term_capital_gain
        - -with_deduction.ordinary
    )


def test_extra_tax_from_rejects_a_negative_deduction() -> None:
    with pytest.raises(AssertionError):
        _tax_module().extra_tax_from(
            MONTH,
            TaxableAmounts(ordinary_income=100),
            TaxableAmounts(
                ordinary_deductions=-1,
                depreciation_recapture=100,
                long_term_capital_gains=100,
            ),
        )
