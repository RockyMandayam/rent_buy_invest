import csv
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml


def to_df(
    cols: Dict[str, List[Any]],
    rows: Optional[List[str]] = None,
    multi_col: bool = False,
) -> pd.DataFrame:
    """
    Args:
        cols: Map from column name to col (list of values)

    Returns:
        pd.DataFrame: DataFrame constructed from given cols
    """
    index = index = pd.Index(rows) if rows else None
    df = pd.DataFrame(data=cols, index=index)
    if multi_col:
        tuples = []
        for col in cols.keys():
            if col.startswith("Rent"):
                category = "Rent"
            elif col.startswith("House"):
                category = "House"
            else:
                raise ValueError(
                    "All columns in projection table must start with 'Rent' or 'House'"
                )
            tuples.append((category, col))
        columns = pd.MultiIndex.from_tuples(tuples)
        df.columns = columns
    return df
