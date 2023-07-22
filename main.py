import argparse

from rent_buy_invest.core.experiment_config import ExperimentConfig

parser = argparse.ArgumentParser(
    prog="rent_buy_invest",
    description="Calculates the long-term financial pros and cons of decisions related to renting a home, buying a house, and investing in the stock market.",
    epilog="See README for more details.",
)
parser.add_argument(
    "experiment_config",
    type=str,
    help="Path (from top-level directory) to experiment config file.",
)
args = parser.parse_args()

if __name__ == "__main__":
    experiment_config = ExperimentConfig.parse(args.experiment_config)
