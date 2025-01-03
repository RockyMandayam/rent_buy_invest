import pytest

from rent_buy_invest.configs.config import Config


class TestConfig:
    def test_init(self) -> None:
        # Config should not be instantiable
        with pytest.raises(TypeError):
            config = Config()
