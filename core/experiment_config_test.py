import jsonschema

from rent_buy_invest.core.experiment_config import ExperimentConfig
from rent_buy_invest.utils import io_utils

TEST_SCHEMA_PATH = "rent_buy_invest/configs/schemas/experiment-config-schema.json"
TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
experiment_config_schema = io_utils.read_json(TEST_SCHEMA_PATH)
experiment_config_kwargs = io_utils.read_yaml(TEST_CONFIG_PATH)
jsonschema.validate(instance=experiment_config_kwargs, schema=experiment_config_schema)
# tests creating ExperimentConfig directly
experiment_config = ExperimentConfig(**experiment_config_kwargs)
# tests creating ExperimentConfig via parse()
experiment_config = ExperimentConfig.parse(TEST_CONFIG_PATH)
