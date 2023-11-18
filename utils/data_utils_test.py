import pandas as pd

from rent_buy_invest.utils import data_utils, io_utils


def test_to_df() -> None:
    # just cols
    cols = {"ints": [0, 1, 2], "bools": [True, True, False], "strings": ["", "a", "bc"]}
    act = data_utils.to_df(cols)
    # exp = pd.DataFrame(data=cols)
    exp_df_project_path = "rent_buy_invest/utils/test_resources/test_to_df_1.pickle"
    # Use the below line to update the test
    # exp.to_pickle(io_utils.get_abs_path(exp_df_project_path))
    exp = pd.read_pickle(io_utils.get_abs_path(exp_df_project_path))
    assert act.equals(exp)

    # cols + rows
    rows = ["first", "second", "third"]
    act = data_utils.to_df(cols, rows)
    # exp = pd.DataFrame(data=cols, index=pd.Index(rows))
    exp_df_project_path = "rent_buy_invest/utils/test_resources/test_to_df_2.pickle"
    # Use the below line to update the test
    # exp.to_pickle(io_utils.get_abs_path(exp_df_project_path))
    exp = pd.read_pickle(io_utils.get_abs_path(exp_df_project_path))
    assert act.equals(exp)

    # cols + rows + multi_col_func
    multi_col_func = (
        lambda col_name: "Category 1" if col_name == "ints" else "Category 2"
    )
    act = data_utils.to_df(cols, rows, multi_col_func)
    # exp = pd.DataFrame(data=cols, index=pd.Index(rows))
    # exp.columns = pd.MultiIndex.from_tuples([("Category 1", "ints"), ("Category 2", "bools"), ("Category 2", "strings")])
    exp_df_project_path = "rent_buy_invest/utils/test_resources/test_to_df_3.pickle"
    # Use the below line to update the test
    # exp.to_pickle(io_utils.get_abs_path(exp_df_project_path))
    exp = pd.read_pickle(io_utils.get_abs_path(exp_df_project_path))
    assert act.equals(exp)
