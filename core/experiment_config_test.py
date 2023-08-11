from rent_buy_invest.core.experiment_config import ExperimentConfig


TEST_CONFIG_PATH = "rent_buy_invest/core/test_resources/test-experiment-config.yaml"
experiment_config = ExperimentConfig.parse(TEST_CONFIG_PATH)
