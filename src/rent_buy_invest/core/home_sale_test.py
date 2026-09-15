import pytest

from rent_buy_invest.core.home_sale import compute_home_sale


def test_compute_home_sale_subtracts_selling_costs_from_the_gain() -> None:
    """Selling costs reduce the gain, not only the cash.

    Until recently some of them reduced only the cash, which taxed the seller on
    a gain larger than the real one. Nothing tested this while it lived inline in
    ``main.py``, so it could have come back silently.
    """
    sale = compute_home_sale(
        final_sale_price=1_000_000,
        purchase_price=600_000,
        selling_costs=60_000,
        part_of_basis_upfront_one_time_cost=15_000,
    )

    assert sale.amount_realized == pytest.approx(1_000_000 - 60_000)
    assert sale.cost_basis == pytest.approx(600_000 + 15_000)
    assert sale.gain == pytest.approx((1_000_000 - 60_000) - (600_000 + 15_000))


def test_compute_home_sale_reports_a_loss_as_a_negative_gain() -> None:
    """A loss is reported as it happened, not hidden as zero.

    Whether it counts for tax is a separate question, answered where the tax is
    worked out.
    """
    sale = compute_home_sale(
        final_sale_price=500_000,
        purchase_price=600_000,
        selling_costs=30_000,
        part_of_basis_upfront_one_time_cost=15_000,
    )

    assert sale.amount_realized == pytest.approx(500_000 - 30_000)
    assert sale.gain == pytest.approx((500_000 - 30_000) - (600_000 + 15_000))
    assert sale.gain < 0


def test_compute_home_sale_gain_is_before_any_exclusion() -> None:
    """The exclusion for a home you lived in is a tax rule applied afterwards.

    A gain well above the exclusion comes back in full here.
    """
    sale = compute_home_sale(
        final_sale_price=2_000_000,
        purchase_price=600_000,
        selling_costs=0,
        part_of_basis_upfront_one_time_cost=0,
    )

    assert sale.gain == pytest.approx(1_400_000)
