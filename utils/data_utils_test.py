import csv
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from rent_buy_invest.utils import data_utils


def test_to_df() -> None:
    # if rows:
    #     return pd.DataFrame(cols, index=pd.Index(rows))
    # return pd.DataFrame(cols)
    cols = {"col1": [1, 2], "col2": [3, 4]}
    df = data_utils.to_df(cols)
