from collections.abc import Callable
from typing import Any

import pandas as pd


def to_df(
    cols: dict[str, list[Any]],
    rows: list[str] | None = None,
    multi_col: bool = False,
) -> pd.DataFrame:
    """
    Args:
        cols: Map from column name to col (list of values)
        rows: Optional list of row names
        multi_col: if True, assumes the col names are of the form "<multicol group 1>: <multicol group 2>"
            where group 1 is like a top-level header and group 2 is like a second-leveel header.
            E.g., "Costs: Financial" would be split into ("Costs", "Financial") in multicolumn

    Returns:
        pd.DataFrame: DataFrame constructed from given cols
    """
    index = index = pd.Index(rows) if rows else None
    df = pd.DataFrame(data=cols, index=index)
    if multi_col:
        tuples = [tuple(col_name.split(": ")) for col_name in cols]
        columns = pd.MultiIndex.from_tuples(tuples)
        df.columns = columns
    return df
