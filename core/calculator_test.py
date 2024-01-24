import pytest

from rent_buy_invest.core.calculator import Calculator
from rent_buy_invest.core.experiment_config_test import EXPERIMENT_CONFIG
from rent_buy_invest.core.initial_state import InitialState


class TestCalculator:
    def test_calculate(self) -> None:
        calculator = Calculator(
            EXPERIMENT_CONFIG.house_config,
            EXPERIMENT_CONFIG.rent_config,
            EXPERIMENT_CONFIG.market_config,
            EXPERIMENT_CONFIG.num_months,
            EXPERIMENT_CONFIG.start_date,
            InitialState(EXPERIMENT_CONFIG.house_config, EXPERIMENT_CONFIG.rent_config),
        )

        # initial state tested separately

        # TODO do an exact comparison of the project vs my by-hand calculations.
        projection = calculator.calculate()

        first_row = projection.iloc[0, :]
        house_value_related_cost_fraction = (
            first_row["House"]["House: Monthly cost tied to house value"]
            / first_row["House"]["House: House value"]
        )

        for row_index in range(projection.shape[0]):
            # for index, row in projection.iterrows():
            # 'House: Monthly cost tied to house value'
            # 'House: Monthly cost tied to inflation'
            # 'House: Monthly mortgage interest payment'
            # 'House: Monthly mortgage equity payment'
            # 'House: Monthly mortgage total payment'
            # 'House: House: Monthly cost of PMI'
            # 'House: Monthly surplus (relative to renting)'
            # 'House: House value'
            # 'House: Equity value'
            # 'House: Investment (excluding house) value'
            # 'Rent: Monthly cost tied to inflation'
            # 'Rent: Monthly surplus (relative to buying a house)'
            # 'Rent: Investment'

            # mortgage interest + mortgage equity = momrtgage
            # print(type(index))
            # print(type(row))
            # print(index)
            # print(row)
            # print(row['House'])
            # print(row['Rent'])
            # print(type(row['House']))
            # assert row['']
            row = projection.iloc[row_index, :]

            # test house_value_related_cost_fraction stays constant over every row
            # TODO check the rel=
            assert row["House"]["House: Monthly cost tied to house value"] / row[
                "House"
            ]["House: House value"] == pytest.approx(
                house_value_related_cost_fraction, rel=0.0001
            )

            # TODO enforce that the mortgage amount is also unchanged on all but last row
            assert (
                row["House"]["House: Monthly mortgage interest payment"]
                + row["House"]["House: Monthly mortgage equity payment"]
                == row["House"]["House: Monthly mortgage total payment"]
            )

            # TODO check that not paying PMI after 20%
            # TODO check house surplus
            # TODO check rent surplus
            assert row["House"]["House: Monthly mortgage interest payment"] + row[
                "House"
            ]["House: Monthly mortgage equity payment"] == pytest.approx(
                row["House"]["House: Monthly mortgage total payment"]
            )
