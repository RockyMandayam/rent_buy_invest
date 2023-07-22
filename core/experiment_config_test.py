from typing import Any, Dict

import yaml

from rent_buy_invest.core.experiment_config import ExperimentConfig
from rent_buy_invest.utils import io_utils

TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
ExperimentConfig.parse(TEST_CONFIG_PATH)
