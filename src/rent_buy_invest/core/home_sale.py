from dataclasses import dataclass


@dataclass(frozen=True)
class HomeSale:
    """What selling a home produces, before any tax, in dollars.

    ``amount_realized`` is what the sale actually brings in: the sale price less
    every cost of selling. It is still owed to the lender first -- the loan is not
    taken out of it -- so it is not the cash you walk away with.

    ``cost_basis`` is what the home cost you for tax purposes: the price you paid
    plus the closing costs that count toward the basis.

    Unlike ``RentalSaleResult``, there is no depreciation: a home you live in is
    never depreciated, so its basis is never reduced.
    """

    amount_realized: float
    cost_basis: float

    @property
    def gain(self) -> float:
        """How much the sale brought in over what the home cost, in dollars.

        **Negative on a loss.** Derived rather than stored, so it cannot drift from
        the two fields it comes from.

        This is the gain as it happened, before any tax rule touches it. Whether a
        loss counts for anything, and how much of a gain is excluded for a home you
        lived in, are both decided where the tax is worked out, not here.
        """
        return self.amount_realized - self.cost_basis


def compute_home_sale(
    final_sale_price: float,
    purchase_price: float,
    selling_costs: float,
    part_of_basis_upfront_one_time_cost: float,
) -> HomeSale:
    """Work out what selling a home brings in, and what it cost for tax purposes.

    Args:
        final_sale_price: what the home sells for at the END of the projection.
        purchase_price: what was paid for the home at the START of the projection.
        selling_costs: every cost the seller pays to sell, at ``final_sale_price``.
            All of it reduces the gain, not just the cash.
        part_of_basis_upfront_one_time_cost: the closing costs paid when buying
            that are added to the cost basis. Loan costs are not among them.
    """
    assert final_sale_price >= 0
    assert purchase_price >= 0
    assert selling_costs >= 0
    assert part_of_basis_upfront_one_time_cost >= 0

    return HomeSale(
        amount_realized=final_sale_price - selling_costs,
        cost_basis=purchase_price + part_of_basis_upfront_one_time_cost,
    )
