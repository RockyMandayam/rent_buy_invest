import argparse
import datetime
import os

from rent_buy_invest.core.experiment_config import ExperimentConfig
from rent_buy_invest.utils import io_utils, path_utils

OVERALL_OUTPUT_DIR = "rent_buy_invest/out/"


def get_args() -> argparse.Namespace:
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
    return args


def make_output_dir() -> str:
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = os.path.join(OVERALL_OUTPUT_DIR, f"experiment_{timestamp_str}")
    output_dir = path_utils.get_abs_path(output_dir)
    os.makedirs(output_dir)
    return output_dir


def main() -> None:
    """Main method; entrypoint for this repo."""

    # get args; set up `--help` and `-h`
    args = get_args()

    # load configs
    experiment_config = ExperimentConfig.parse(args.experiment_config)
    num_months = experiment_config.num_months
    market_config = experiment_config.market_config
    rent_config = experiment_config.rent_config
    house_config = experiment_config.house_config

    # create output dir
    output_dir = make_output_dir()

    # calculate initial state
    # TODO are there costs? Moving? Security deposit?
    rent_one_time_costs = 0
    house_one_time_costs = house_config.get_upfront_one_time_cost()
    house_invested_in_house = house_config.get_down_payment()
    # TODO what if rent_one_time_costs is non-zero? Can this be negative?
    rent_invested_in_market = (
        house_one_time_costs + house_invested_in_house - rent_one_time_costs
    )
    # initial state csv rows to write
    initial_state = [
        [None, "Rent", "House"],
        ["One-time costs", rent_one_time_costs, house_one_time_costs],
        [
            "Invested (in market or house)",
            rent_invested_in_market,
            house_invested_in_house,
        ],
    ]
    initial_state_file_path = os.path.join(output_dir, "initial_state.csv")
    io_utils.write_csv(initial_state_file_path, initial_state)

    # project forward in time
    # some numbers can be calculated ahead of time
    rent_monthly_costs = rent_config.get_monthly_costs_of_renting(num_months)
    # calculate the rest month by month
    projection = []
    for month in range(experiment_config.num_months):
        month_row = [month, rent_monthly_costs[month]]
        projection.append(month_row)
    projection_file_path = os.path.join(output_dir, "projection.csv")
    io_utils.write_csv(projection_file_path, projection)


if __name__ == "__main__":
    main()
