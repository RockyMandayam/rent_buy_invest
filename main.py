import argparse

from rent_buy_invest.core.experiment_config import ExperimentConfig

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

def main() -> None:
    """ Main method; entrypoint for this repo. """
    
    # get args; set up `--help` and `-h`
    args = get_args()

    # load configs
    experiment_config = ExperimentConfig.parse(args.experiment_config)
    num_months = experiment_config.num_months
    market_config = experiment_config.market_config
    rent_config = experiment_config.rent_config
    house_config = experiment_config.house_config


    # calculate starting points
    # TODO are there costs? Moving? Security deposit?
    rent_one_time_costs = 0 
    house_one_time_costs = house_config.get_upfront_one_time_cost()
    house_invested_in_house = house_config.get_down_payment()
    # TODO what if rent_one_time_costs is non-zero? Can this be negative?
    rent_invested_in_market = house_one_time_costs + house_invested_in_house - rent_one_time_costs
    
    # # some numbers can be calculated ahead of time

    # # for month in range(experiment_config.num_months):


if __name__ == "__main__":
    main()
