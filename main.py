import argparse
import datetime
import os
from typing import Any, Dict, List, Optional

import yaml

from rent_buy_invest.core.experiment_config import ExperimentConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.utils import io_utils

OVERALL_OUTPUT_DIR = "rent_buy_invest/out/"


# TODO test this file


def _get_args() -> argparse.Namespace:
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


def _make_output_dir() -> str:
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = os.path.join(OVERALL_OUTPUT_DIR, f"experiment_{timestamp_str}")
    io_utils.make_dirs(output_dir)
    return output_dir


def _write_output_yaml(output_dir: str, filename: str, obj: Any) -> None:
    path = os.path.join(output_dir, filename)
    io_utils.write_yaml(path, obj)


def _write_output_csv(
    output_dir: str, filename: str, rows: List[List[Optional[Any]]]
) -> None:
    path = os.path.join(output_dir, filename)
    io_utils.write_csv(path, rows)


def main() -> None:
    """Main method; entrypoint for this repo."""

    # get args; set up `--help` and `-h`
    args = _get_args()

    # load configs
    experiment_config = ExperimentConfig.parse(args.experiment_config)
    num_months = experiment_config.num_months
    market_config = experiment_config.market_config
    rent_config = experiment_config.rent_config
    house_config = experiment_config.house_config

    # create output dir
    output_dir = _make_output_dir()

    # dump configs in output dir (to keep record of configs)
    _write_output_yaml(output_dir, "configs.yaml", experiment_config)

    # calculate initial state
    initial_state = InitialState(house_config)
    _write_output_csv(output_dir, "initial_state.csv", initial_state.to_csv())

    # project forward in time
    # some numbers can be calculated ahead of time, others month by month
    rent_monthly_costs = rent_config.get_monthly_costs_of_renting(num_months)
    rent_investment_monthly = market_config.get_pretax_monthly_wealth(
        initial_state.rent_invested, num_months
    )
    house_values = house_config.get_monthly_house_values(num_months)
    house_monthly_costs_related_to_house_value = (
        house_config.get_house_value_related_monthly_costs(num_months)
    )
    house_monthly_costs_related_to_inflation = (
        # TODO don't use rent inflation maybe? Use something else for utilities for rent and house?
        house_config.get_inflation_related_monthly_costs(
            rent_config.annual_rent_inflation_rate, num_months
        )
    )

    projection = [
        [
            None,
            "Rent: monthly cost",
            "Rent: market investment",
            "House: house value related monthly cost",
            "House: house value",
            "House: inflation related monthly cost",
        ]
    ]
    for month in range(experiment_config.num_months):
        month_row = [
            month,
            rent_monthly_costs[month],
            rent_investment_monthly[month],
            house_monthly_costs_related_to_house_value[month],
            house_values[month],
            house_monthly_costs_related_to_inflation[month],
        ]
        projection.append(month_row)
    _write_output_csv(output_dir, "projection.csv", projection)


if __name__ == "__main__":
    main()
