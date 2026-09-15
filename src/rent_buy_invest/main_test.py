import sys

import pytest

from rent_buy_invest.main import _cap_gains_from_selling_investments, _get_args
from rent_buy_invest.utils.data_utils import to_df


def _projection(balances: list[float], bases: list[float]):
    """A minimal stand-in for the projection, with just the columns that matter."""
    return to_df(
        {
            "Rent: Invested (Pre-Tax)": balances,
            "Rent: Invested Cost Basis": bases,
        },
        multi_col=True,
    )


def test_gain_is_the_final_balance_less_the_final_basis() -> None:
    """Only what the money earned is gain; what was paid in is not."""
    # opens at 1,000, 300 more paid in along the way, and ends at 1,500
    projection = _projection([1000, 1150, 1310, 1500], [1000, 1100, 1200, 1300])

    assert _cap_gains_from_selling_investments(projection, "Rent") == pytest.approx(200)


def test_gain_uses_the_final_row_only() -> None:
    """Earlier rows are history; the sale is priced on where the account ended."""
    projection = _projection([1000, 5000, 9000, 1500], [1000, 1000, 1000, 1300])

    assert _cap_gains_from_selling_investments(projection, "Rent") == pytest.approx(200)


def test_a_loss_is_reported_as_no_gain() -> None:
    """TODO: losses are floored rather than deducted; see the helper's docstring."""
    projection = _projection([1000, 900, 800, 700], [1000, 1000, 1000, 1000])

    assert _cap_gains_from_selling_investments(projection, "Rent") == 0


def test_a_balance_that_is_all_basis_is_never_taxed() -> None:
    """A flat market that only received deposits, or dividends already taxed."""
    projection = _projection([0, 100, 200, 300], [0, 100, 200, 300])

    assert _cap_gains_from_selling_investments(projection, "Rent") == 0


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
