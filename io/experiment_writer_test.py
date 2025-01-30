import pytest

from rent_buy_invest.io.experiment_writer import ExperimentWriter


class TestExperimentWriter:
    def test_init(self) -> None:
        with pytest.raises(AssertionError):
            ExperimentWriter("invalid space")
        with pytest.raises(AssertionError):
            ExperimentWriter("invalid/slash")
        experiment_writer = ExperimentWriter("TestExperimentWriter_test")
