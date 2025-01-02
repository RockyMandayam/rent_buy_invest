import argparse
import datetime
import os
from typing import Any

import openpyxl
import pandas as pd

from rent_buy_invest.core.calculator import Calculator
from rent_buy_invest.core.experiment_config import ExperimentConfig
from rent_buy_invest.core.initial_state import InitialState
from rent_buy_invest.utils import io_utils

OVERALL_OUTPUT_DIR = "rent_buy_invest/out/"


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rent_buy_invest",
        description="Calculates the long-term financial pros and cons of decisions related to renting a home, buying a house, and investing in the stock market.",
        epilog="See README for more details.",
    )
    parser.add_argument(
        "experiment_config",
        type=str,
        help="Path (from 'rent_buy_invest' directory) to experiment config file.",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        help="Name of the experiment. Output folder will be 'out/<experiment_name>/<timestamp>'; defaults to 'experiment'",
    )
    args = parser.parse_args()
    assert args.experiment_config.endswith(".yaml") or args.experiment.config_endswith(
        ".yml"
    ), "Experiment config file must end in '.yaml' or '.yml'"
    if not args.experiment_name:
        args.experiment_name = "unnamed_experiment"
    assert all(
        c.isalpha() or c.isdigit() or c in "_-" for c in args.experiment_name
    ), f"Provide an experiment name which only contains characters, digits, underscores, and/or dashes; received '{args.experiment_name}'"
    return args


def _make_output_dir(experiment_name: str) -> str:
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = os.path.join(OVERALL_OUTPUT_DIR, experiment_name, timestamp_str)
    io_utils.make_dirs(output_dir)
    return output_dir


def _write_output_yaml(output_dir: str, filename: str, obj: Any) -> None:
    path = os.path.join(output_dir, filename)
    io_utils.write_yaml(path, obj)


def _write_output_xlsx_df(
    output_dir: str, filename: str, df: pd.DataFrame, num_header_rows=0
) -> None:
    path = os.path.join(output_dir, filename)
    io_utils.write_xlsx_df(path, df)
    wb = openpyxl.load_workbook(path)
    ws = wb["Sheet1"]
    ws.column_dimensions["A"].width = 15
    ws.freeze_panes = f"B{num_header_rows+1}"
    max_num_cols_with_data = 14
    for i in range(max_num_cols_with_data):
        col_name = chr(ord("B") + i)
        # ws.column_dimensions[col_name].number_format = "$#,##0.00"
        ws.column_dimensions[col_name].width = 18
        for header_row in range(1, num_header_rows + 1):
            ws[f"{col_name}{header_row}"].alignment = openpyxl.styles.Alignment(
                horizontal="left"
            )
        for cell in ws[col_name]:
            cell.number_format = "$#,##0.00"
    wb.save(path)


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
    start_date = experiment_config.start_date

    # create output dir
    output_dir = _make_output_dir(args.experiment_name)

    # dump configs in output dir (to keep record of configs)
    _write_output_yaml(output_dir, "configs.yaml", experiment_config)

    # calculate initial state
    initial_state = InitialState.from_configs(house_config, rent_config)
    _write_output_xlsx_df(
        output_dir, "initial_state.xlsx", initial_state.get_df(), num_header_rows=1
    )

    # project forward in time
    calculator = Calculator(
        house_config, rent_config, market_config, num_months, start_date, initial_state
    )
    projection = calculator.calculate()
    _write_output_xlsx_df(output_dir, "projection.xlsx", projection, num_header_rows=2)


if __name__ == "__main__":
    main()
