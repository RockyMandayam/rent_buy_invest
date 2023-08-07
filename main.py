import argparse
import datetime
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml

from rent_buy_invest.core.calculator import Calculator
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


def _write_output_csv_df(output_dir: str, filename: str, df: pd.DataFrame) -> None:
    path = os.path.join(output_dir, filename)
    io_utils.write_csv_df(path, df)


def format_projection(
    projection: Tuple[Tuple[str, List[float]]], num_months: int
) -> List[List[float]]:
    formatted = []
    # add title row
    formatted.append([None] + [col_name for col_name, _ in projection])
    # add data
    for month in range(num_months):
        formatted.append([month] + [data[month] for _, data in projection])
    return formatted


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
    _write_output_csv_df(output_dir, "initial_state.csv", initial_state.get_df())

    # project forward in time
    calculator = Calculator(
        house_config, rent_config, market_config, num_months, initial_state
    )
    projection = calculator.calculate()
    _write_output_csv_df(output_dir, "projection.csv", projection)

    # # first start with rent
    # rent_calculator = RentCalculator(
    #     rent_config, market_config, num_months, initial_state
    # )
    # rent_projection = rent_calculator.calculate()
    # _write_output_csv_df(output_dir, "rent_projection.csv", rent_projection)

    # # now do house
    # house_calculator = HouseCalculator(
    #     house_config, rent_config, num_months, initial_state
    # )
    # house_projection = house_calculator.calculate()
    # _write_output_csv_df(output_dir, "house_projection.csv", house_projection)


if __name__ == "__main__":
    main()
