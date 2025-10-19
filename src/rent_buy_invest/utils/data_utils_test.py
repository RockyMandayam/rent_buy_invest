import pandas as pd

from rent_buy_invest.io import io_utils
from rent_buy_invest.utils import data_utils

COLS = {
    "Category 1: ints": [0, 1, 2],
    "Category 2: bools": [True, True, False],
    "Category 2: strings": ["", "a", "bc"],
}
ROWS = ["first", "second", "third"]
MULTICOL_TUPLES = [
    ("Category 1", "ints"),
    ("Category 2", "bools"),
    ("Category 2", "strings"),
]


def test_to_df_cols() -> None:
    act = data_utils.to_df(COLS)
    exp_df_project_path = "rent_buy_invest/utils/test_resources/test_to_df_1.pickle"

    # Use the below 2 lines to update the test
    # exp = pd.DataFrame(data=COLS)
    # exp.to_pickle(io_utils.get_abs_path(exp_df_project_path))

    exp = pd.read_pickle(io_utils.get_abs_path(exp_df_project_path))
    assert act.equals(exp)


def test_to_df_cols_rows() -> None:
    act = data_utils.to_df(COLS, ROWS)
    exp_df_project_path = "rent_buy_invest/utils/test_resources/test_to_df_2.pickle"

    # Use the below 2 lines to update the test
    # exp = pd.DataFrame(data=COLS, index=pd.Index(ROWS))
    # exp.to_pickle(io_utils.get_abs_path(exp_df_project_path))

    exp = pd.read_pickle(io_utils.get_abs_path(exp_df_project_path))
    assert act.equals(exp)


def test_to_df_cols_rows_multicol() -> None:
    act = data_utils.to_df(COLS, ROWS, multi_col=True)
    exp_df_project_path = "rent_buy_invest/utils/test_resources/test_to_df_3.pickle"

    # Use the below 3 lines to update the test
    # exp = pd.DataFrame(data=COLS, index=pd.Index(ROWS))
    # exp.columns = pd.MultiIndex.from_tuples(MULTICOL_TUPLES)
    # exp.to_pickle(io_utils.get_abs_path(exp_df_project_path))

    exp = pd.read_pickle(io_utils.get_abs_path(exp_df_project_path))
    assert act.equals(exp)
