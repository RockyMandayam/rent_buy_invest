from typing import Any, Dict

import yaml

from rent_buy_invest.core.general_config import GeneralConfig
from rent_buy_invest.utils import io_utils, path_utils


class TestGeneralConfig:
    def test_parse(self) -> None:
        filename = path_utils.get_abs_path(
            "rent_buy_invest/core/test_resources/test-general-config.yaml"
        )
        GeneralConfig.parse(filename)
