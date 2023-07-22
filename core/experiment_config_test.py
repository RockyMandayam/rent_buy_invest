from typing import Any, Dict

import yaml

from rent_buy_invest.core.experiment_config import ExperimentConfig
from rent_buy_invest.utils import io_utils, path_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
filename = path_utils.get_abs_path(TEST_CONFIG_PATH)
ExperimentConfig.parse(filename)
