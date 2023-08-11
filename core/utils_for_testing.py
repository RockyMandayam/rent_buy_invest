import copy
from typing import List, Type

import pytest

from rent_buy_invest.core.config import Config


def check_float_field(clz: Type, config_kwargs: Config, field_keys: List, allow_negative: bool = True) -> None:
    # TODO test this
    # TODO document this
    assert field_keys, "field_keys must be a non-empty list"
    config_kwargs = copy.deepcopy(config_kwargs)
    field = config_kwargs
    for i in range(len(field_keys) - 1):# in field_keys:
        # field = field[field_key]
        field = field[field_keys[i]]
    for val in [float('nan'), float('inf'), float('-inf')]:
        field[field_keys[-1]] = float('nan')
        with pytest.raises(AssertionError):
            clz(**config_kwargs)
