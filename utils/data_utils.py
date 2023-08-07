import csv
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml


def to_df(cols: Dict[str, List[Any]], rows: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Args:
        cols: Map from column name to col (list of values)

    Returns:
        pd.DataFrame: DataFrame constructed from given cols
    """
    if rows:
        return pd.DataFrame(cols, index=pd.Index(rows))
    return pd.DataFrame(cols)
