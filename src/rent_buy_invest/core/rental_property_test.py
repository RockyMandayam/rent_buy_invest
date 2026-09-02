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
        buy_config.sale_price + buy_config.get_part_of_basis_upfront_one_time_cost()
    )
    assert rental_property.depreciable_basis == pytest.approx(expected)
    # land is excluded, so the basis is strictly less than what was paid
    assert rental_property.depreciable_basis < buy_config.sale_price


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


def test_taxable_income_subtracts_interest_and_depreciation_not_principal() -> None:
    rental_property = _rental_property()

    for month in (0, 1, 200, NUM_MONTHS):
        assert rental_property.monthly_taxable_income[month] == pytest.approx(
            rental_property.monthly_rental_income[month]
            - rental_property.monthly_operating_expenses[month]
            - rental_property.monthly_mortgage_interest[month]
            - rental_property.monthly_depreciation[month]
        )


def test_taxable_income_is_below_cash_flow_while_depreciating() -> None:
    """Depreciation costs no cash, and principal is not deductible.

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
