from copy import deepcopy

import pytest

from rent_buy_invest.configs.buy_config import BuyConfig
from rent_buy_invest.core.depreciation import RESIDENTIAL_DEPRECIATION_MONTHS
from rent_buy_invest.core.rental_property import RentalProperty
from rent_buy_invest.io import io_utils

BUY_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-buy-config.yaml"
PRIMARY_RESIDENCE_CONFIG_PATH = (
    "rent_buy_invest/core/test_resources/test-primary-residence-buy-config.yaml"
)
ANNUAL_INFLATION_RATE = 0.03
# what a single filer could exclude on a home they had lived in; never applies here
PRIMARY_RESIDENCE_EXCLUSION = 250_000
NUM_MONTHS = 360


def _rental_property(num_months: int = NUM_MONTHS) -> RentalProperty:
    return RentalProperty(
        BuyConfig.parse(BUY_CONFIG_PATH), ANNUAL_INFLATION_RATE, num_months
    )


def test_rejects_a_home_that_is_not_rented_out() -> None:
    primary_residence = BuyConfig.parse(PRIMARY_RESIDENCE_CONFIG_PATH)
    with pytest.raises(AssertionError):
        RentalProperty(primary_residence, ANNUAL_INFLATION_RATE, NUM_MONTHS)


def test_rejects_a_zero_length_projection() -> None:
    with pytest.raises(AssertionError):
        _rental_property(num_months=0)


def test_every_projection_covers_month_zero_through_num_months() -> None:
    rental_property = _rental_property()
    expected_length = NUM_MONTHS + 1

    for name in (
        "monthly_mortgage_interest",
        "monthly_mortgage_principal",
        "monthly_mortgage_payment",
        "monthly_depreciation",
        "monthly_rental_income",
        "monthly_operating_expenses",
        "monthly_pretax_cash_flow",
        "monthly_taxable_income",
    ):
        assert len(getattr(rental_property, name)) == expected_length, name


def test_depreciable_basis_is_the_buildings_share_of_the_cost() -> None:
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    rental_property = _rental_property()

    expected = buy_config.rental_income_config.building_fraction_of_value * (
        buy_config.purchase_price + buy_config.get_part_of_basis_upfront_one_time_cost()
    )
    assert rental_property.depreciable_basis == pytest.approx(expected)
    # land is excluded, so the basis is strictly less than what was paid
    assert rental_property.depreciable_basis < buy_config.purchase_price


def test_depreciation_is_level_then_stops() -> None:
    rental_property = _rental_property(num_months=RESIDENTIAL_DEPRECIATION_MONTHS + 12)
    monthly = rental_property.monthly_depreciation

    assert monthly[0] > 0
    assert monthly[0] == monthly[1] == monthly[100]
    assert monthly[RESIDENTIAL_DEPRECIATION_MONTHS] == 0
    # the whole basis is deducted, no more and no less
    assert rental_property.accumulated_depreciation(
        RESIDENTIAL_DEPRECIATION_MONTHS + 12
    ) == pytest.approx(rental_property.depreciable_basis)


def test_accumulated_depreciation_grows_then_levels_off() -> None:
    rental_property = _rental_property(num_months=RESIDENTIAL_DEPRECIATION_MONTHS + 12)

    assert rental_property.accumulated_depreciation(0) == pytest.approx(
        rental_property.monthly_depreciation[0]
    )
    assert rental_property.accumulated_depreciation(
        23
    ) > rental_property.accumulated_depreciation(11)
    # nothing accrues once the property is fully depreciated
    assert rental_property.accumulated_depreciation(
        RESIDENTIAL_DEPRECIATION_MONTHS - 1
    ) == rental_property.accumulated_depreciation(RESIDENTIAL_DEPRECIATION_MONTHS + 12)


def test_mortgage_payment_is_interest_plus_principal() -> None:
    rental_property = _rental_property()

    for month in range(NUM_MONTHS + 1):
        assert rental_property.monthly_mortgage_payment[month] == pytest.approx(
            rental_property.monthly_mortgage_interest[month]
            + rental_property.monthly_mortgage_principal[month]
        )


def test_operating_expenses_exclude_the_whole_mortgage() -> None:
    """Neither half of the mortgage payment belongs in operating expenses.

    Principal because it is not deductible, interest because each of the two
    figures needs a different part of the payment and so tracks it separately.
    """
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    rental_property = _rental_property()

    expected_first_month = (
        buy_config.get_home_value_related_monthly_costs(NUM_MONTHS)[0]
        + buy_config.get_inflation_related_monthly_costs(
            ANNUAL_INFLATION_RATE, NUM_MONTHS
        )[0]
    )
    # the test config puts 20% down, so no mortgage insurance is ever owed and
    # operating expenses are exactly the two cost streams
    assert rental_property.monthly_operating_expenses[0] == pytest.approx(
        expected_first_month
    )
    # and there is a real mortgage being left out, not a zero one, so the
    # equality above is not passing vacuously
    assert rental_property.monthly_mortgage_interest[0] > 0
    assert rental_property.monthly_mortgage_principal[0] > 0


def test_cash_flow_subtracts_the_whole_mortgage_payment() -> None:
    rental_property = _rental_property()

    for month in (0, 1, 200, NUM_MONTHS):
        assert rental_property.monthly_pretax_cash_flow[month] == pytest.approx(
            rental_property.monthly_rental_income[month]
            - rental_property.monthly_operating_expenses[month]
            - rental_property.monthly_mortgage_payment[month]
        )


def test_taxable_income_subtracts_interest_deprec_and_points_not_principal() -> None:
    rental_property = _rental_property()

    for month in (0, 1, 200, NUM_MONTHS):
        assert rental_property.monthly_taxable_income[month] == pytest.approx(
            rental_property.monthly_rental_income[month]
            - rental_property.monthly_operating_expenses[month]
            - rental_property.monthly_mortgage_interest[month]
            - rental_property.monthly_depreciation[month]
            - rental_property.monthly_discount_points_deduction[month]
        )


def test_taxable_income_is_below_cash_flow_while_depreciating() -> None:
    """Depreciation and points cost no cash, and principal is not deductible.

    Their difference is why a rental can hand you money every month and still
    report a loss. This holds while the property is still being depreciated.
    """
    rental_property = _rental_property()

    for month in (0, 100, 300):
        difference = (
            rental_property.monthly_pretax_cash_flow[month]
            - rental_property.monthly_taxable_income[month]
        )
        assert difference == pytest.approx(
            rental_property.monthly_depreciation[month]
            + rental_property.monthly_discount_points_deduction[month]
            - rental_property.monthly_mortgage_principal[month]
        )


def test_rental_income_waits_out_the_waiting_period() -> None:
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    waiting_period = buy_config.rental_income_config.rental_income_waiting_period_months
    rental_property = _rental_property()

    assert all(
        income == 0 for income in rental_property.monthly_rental_income[:waiting_period]
    )
    assert rental_property.monthly_rental_income[waiting_period] > 0
    # while no rent is coming in, the property can only cost money
    assert rental_property.monthly_pretax_cash_flow[0] < 0


def test_paid_off_mortgage_leaves_only_operating_expenses() -> None:
    config_kwargs = io_utils.read_yaml(BUY_CONFIG_PATH)
    config_kwargs = deepcopy(config_kwargs)
    config_kwargs["down_payment_fraction"] = 1.0  # bought outright, no loan
    rental_property = RentalProperty(
        BuyConfig(**config_kwargs), ANNUAL_INFLATION_RATE, NUM_MONTHS
    )

    assert all(payment == 0 for payment in rental_property.monthly_mortgage_payment)
    assert all(interest == 0 for interest in rental_property.monthly_mortgage_interest)
    for month in (0, 200, NUM_MONTHS):
        assert rental_property.monthly_pretax_cash_flow[month] == pytest.approx(
            rental_property.monthly_rental_income[month]
            - rental_property.monthly_operating_expenses[month]
        )


def test_sale_rejects_a_month_outside_the_projection() -> None:
    rental_property = _rental_property()

    with pytest.raises(AssertionError):
        rental_property.sale(700_000, NUM_MONTHS + 1)
    with pytest.raises(AssertionError):
        rental_property.sale(700_000, -1)
    with pytest.raises(AssertionError):
        rental_property.sale(-1, NUM_MONTHS)


def test_sale_reduces_the_basis_by_the_depreciation_taken() -> None:
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    rental_property = _rental_property()
    month = 120

    result = rental_property.sale(700_000, month)

    expected_original = (
        buy_config.purchase_price + buy_config.get_part_of_basis_upfront_one_time_cost()
    )
    assert result.original_basis == pytest.approx(expected_original)
    assert result.accumulated_depreciation == pytest.approx(
        rental_property.accumulated_depreciation(month)
    )
    # every dollar deducted is a dollar of cost already recovered, so it leaves
    # the basis
    assert result.adjusted_basis == pytest.approx(
        result.original_basis - result.accumulated_depreciation
    )
    assert result.adjusted_basis < result.original_basis


def test_sale_splits_the_gain_into_recapture_then_capital_gain() -> None:
    rental_property = _rental_property()
    result = rental_property.sale(700_000, 120)

    assert result.total_gain > 0
    assert result.amount_realized == pytest.approx(
        result.final_sale_price - result.deductible_selling_costs
    )
    assert result.total_gain == pytest.approx(
        result.amount_realized - result.adjusted_basis
    )
    # the two pieces account for the whole gain, nothing lost or double counted
    assert (
        result.depreciation_recapture_gain + result.long_term_capital_gain
    ) == pytest.approx(result.total_gain)
    # recapture is filled first, up to the depreciation taken
    assert result.depreciation_recapture_gain == pytest.approx(
        result.accumulated_depreciation
    )


def test_sale_capital_gain_equals_the_gain_without_any_depreciation() -> None:
    """The split separates real appreciation from deductions being handed back.

    Whatever is left after recapture is exactly the gain there would have been if
    the property had never been depreciated at all.
    """
    rental_property = _rental_property()
    result = rental_property.sale(700_000, 120)

    assert result.long_term_capital_gain == pytest.approx(
        result.amount_realized - result.original_basis
    )


def test_sale_recapture_is_capped_by_the_gain_not_the_depreciation() -> None:
    # a small gain, well under the depreciation taken by then
    rental_property = _rental_property()
    month = 300
    accumulated = rental_property.accumulated_depreciation(month)
    # sell for exactly what was paid: the only gain is the depreciation that
    # reduced the basis below the purchase price
    result = rental_property.sale(rental_property.buy_config.purchase_price, month)

    assert 0 < result.total_gain < accumulated
    assert result.depreciation_recapture_gain == pytest.approx(result.total_gain)
    assert result.long_term_capital_gain == 0


def test_sale_below_adjusted_basis_reports_a_negative_gain() -> None:
    """A loss is reported rather than floored, so the tax layer can decide.

    Nothing is recaptured or taxed when there is no gain.
    """
    rental_property = _rental_property()
    result = rental_property.sale(100_000, 120)

    assert result.total_gain < 0
    assert result.depreciation_recapture_gain == 0
    assert result.long_term_capital_gain == 0


def test_sale_cash_proceeds_ignore_the_gain_calculation() -> None:
    rental_property = _rental_property()
    month = 120
    result = rental_property.sale(700_000, month)

    assert result.loan_payoff == pytest.approx(
        rental_property._amortization_schedule.starting_balances[month]
    )
    # both kinds of selling cost are money out, even though only one of them
    # reduces the gain
    assert result.pretax_cash_proceeds == pytest.approx(
        result.final_sale_price
        - result.deductible_selling_costs
        - result.nondeductible_selling_costs
        - result.loan_payoff
    )
    assert result.nondeductible_selling_costs > 0
    assert result.pretax_cash_proceeds != pytest.approx(result.total_gain)


def test_sale_never_applies_the_primary_residence_exclusion() -> None:
    """The tax-free gain on a home you lived in never applies to a rental."""
    rental_property = _rental_property()
    # priced so the gain clearly exceeds the 250k a single filer could exclude
    # on a home they had lived in
    result = rental_property.sale(900_000, 120)

    assert result.total_gain > PRIMARY_RESIDENCE_EXCLUSION
    # the whole gain survives: nothing is carved out before the recapture split
    assert result.total_gain == pytest.approx(
        result.amount_realized - result.adjusted_basis
    )
    assert (
        result.depreciation_recapture_gain + result.long_term_capital_gain
    ) == pytest.approx(result.total_gain)


def test_discount_points_reduce_taxable_income_but_not_cash() -> None:
    """The cash left at closing; only the deduction is spread over the term."""
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    rental_property = _rental_property()

    fee = (
        buy_config.mortgage_discount_points_fee_fraction
        * buy_config.initial_loan_amount
    )
    expected_monthly = round(fee / buy_config.mortgage_term_months, 2)
    assert rental_property.monthly_discount_points_deduction[0] == expected_monthly

    # the same month with the points deduction removed would show identical cash
    # flow, so nothing here touched the bank account
    assert rental_property.monthly_pretax_cash_flow[0] == pytest.approx(
        rental_property.monthly_rental_income[0]
        - rental_property.monthly_operating_expenses[0]
        - rental_property.monthly_mortgage_payment[0]
    )


def test_discount_points_stop_deducting_when_the_loan_term_ends() -> None:
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    term = buy_config.mortgage_term_months
    rental_property = _rental_property(num_months=term + 12)

    assert rental_property.monthly_discount_points_deduction[term - 1] > 0
    assert rental_property.monthly_discount_points_deduction[term] == 0


def test_sale_reports_the_points_not_yet_deducted() -> None:
    """Selling ends the loan early, so the rest of the points come due at once."""
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    rental_property = _rental_property()
    month = 120

    result = rental_property.sale(700_000, month)
    fee = (
        buy_config.mortgage_discount_points_fee_fraction
        * buy_config.initial_loan_amount
    )
    deducted_so_far = sum(
        rental_property.monthly_discount_points_deduction[: month + 1]
    )

    assert result.unamortized_discount_points > 0
    # every dollar paid is either already deducted or deductible now
    assert deducted_so_far + result.unamortized_discount_points == pytest.approx(fee)
    # it is an ordinary deduction, so it is kept out of the gain entirely
    assert result.total_gain == pytest.approx(
        result.amount_realized - result.adjusted_basis
    )


def test_sale_after_the_loan_term_leaves_no_points_outstanding() -> None:
    buy_config = BuyConfig.parse(BUY_CONFIG_PATH)
    term = buy_config.mortgage_term_months
    rental_property = _rental_property(num_months=term + 12)

    result = rental_property.sale(700_000, term + 12)
    assert result.unamortized_discount_points == 0
