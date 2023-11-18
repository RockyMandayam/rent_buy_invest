from typing import Any, Callable, Dict, List, Optional

import pandas as pd


def to_df(
    cols: Dict[str, List[Any]],
    rows: Optional[List[str]] = None,
    multi_col_func: Optional[Callable[[str], str]] = None,
) -> pd.DataFrame:
    """
    Args:
        cols: Map from column name to col (list of values)
        rows: Optional list of row names
        multi_col_func: Optional function that takes in the col name and outputs the col category.

    Returns:
        pd.DataFrame: DataFrame constructed from given cols
    """
    index = index = pd.Index(rows) if rows else None
    df = pd.DataFrame(data=cols, index=index)
    if multi_col_func:
        tuples = [(multi_col_func(col_name), col_name) for col_name in cols]
        columns = pd.MultiIndex.from_tuples(tuples)
        df.columns = columns
    return df
