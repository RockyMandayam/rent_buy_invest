import math

from rent_buy_invest.configs.config import Config
from rent_buy_invest.utils import math_utils

DEFAULT_VALIDATE_NON_REGRESSIVE_TAX_BRACKETS = True


class MarketConfig(Config):
    """Stores market config.

    Class attributes:
        schema_path (str): Market config schema path

    Instance Attributes:
        self.market_rate_of_return: ANNUAL rate of return in the
            market, as a decimal
        self.tax_brackets: A TaxBrackets object representing income tax rates (which are also short term capital gains tax rates)
        self.long_term_capital_gains_tax_brackets: A TaxBrackets object representing long term capital gains tax rates

    """

    MAX_MARKET_RATE_OF_RETURN = 0.5

    @classmethod
    def schema_path(cls) -> str:
        return "rent_buy_invest/configs/schemas/market-config-schema.json"

    class TaxBrackets:
        """Stores tax bracket config.

        Attributes:
            self.tax_brackets (list[dict[str, float]]): A list of tax brackets,
                where each bracket contains two keys, "upper_limit" and "tax_rate".
                "tax_rate" is the marginal tax rate of that bracket. "upper_limit"
                is the upper income limit of that bracket (beyond that limit, the
                next tax bracket begins). This list is ordered from lowest tax
                bracket to highest tax bracket. The highest tax bracket will have
                an upper limit of infinity.
            self.validate_non_regressive_tax_brackets: If True, validate that the tax brackets
                are non-regressive (i.e., the tax rate never decreases as the tax bracket increases)
        """

        def __init__(
            self,
            tax_brackets: list[dict[str, float]],
            validate_non_regressive_tax_brackets: bool,
        ) -> None:
            """Initializes the class.

            To see why I don't use yaml tags, see the docstring for __init__
            in Config.
            """
            self.tax_brackets: list[dict[str, float]] = tax_brackets
            self.validate_non_regressive_tax_brackets = (
                validate_non_regressive_tax_brackets
            )
            self._validate()

        def _validate(self) -> None:
            """Sanity checks the configs.

            Raises:
                AssertionError: If any tax brackets configs are invalid
            """
            assert self.tax_brackets, "Tax brackets must not be null or empty"
            upper_limit = 0
            prev_tax_rate = 0
            for i, bracket in enumerate(self.tax_brackets):
                if i == len(self.tax_brackets) - 1:
                    assert bracket["upper_limit"] == float(
                        "inf"
                    ), "The last tax bracket's upper limit must be infinity."
                else:
                    assert (
                        math.isfinite(bracket["upper_limit"])
                        and bracket["upper_limit"] > 0
                    ), "All tax brackets except the last one must have an upper limit that is positive and non-infinite."
                assert (
                    math.isfinite(bracket["tax_rate"])
                    and bracket["tax_rate"] >= 0
                    and bracket["tax_rate"] <= 1
                ), "Tax bracket's tax rate must be finite and between 0 and 1 inclusive."
                assert (
                    bracket["upper_limit"] > upper_limit
                ), "Tax brackets must be listed in order."
                if self.validate_non_regressive_tax_brackets:
                    assert (
                        bracket["tax_rate"] >= prev_tax_rate
                    ), "Tax brackets must have non-decreasing tax rates"
                    prev_tax_rate = bracket["tax_rate"]
                upper_limit = bracket["upper_limit"]

        def _get_marginal_income_tax_rate(self, income: float) -> float:
            lower_limit = 0
            for bracket in self.tax_brackets:
                upper_limit = bracket["upper_limit"]
                if income >= lower_limit and income <= upper_limit:
                    return bracket["tax_rate"]
                lower_limit = upper_limit
            assert False

        def _get_income_tax(self, income: float, deduction: float = 0) -> float:
            """Calculates tax owed given income.

            Args:
                income: non-negative income

            Returns:
                tax: non-negative tax owed
            """
            tax = 0
            lower_limit = 0
            deduction = min(deduction, income)
            income -= deduction
            for bracket in self.tax_brackets:
                if income < lower_limit:
                    break
                tax_rate = bracket["tax_rate"]
                upper_limit = bracket["upper_limit"]
                if income <= upper_limit:
                    tax += tax_rate * (income - lower_limit)
                    break
                tax += tax_rate * (upper_limit - lower_limit)
                lower_limit = upper_limit
            return tax

    def __init__(
        self,
        market_rate_of_return: float,
        tax_brackets: dict[str, dict],
        validate_non_regressive_tax_brackets: bool = DEFAULT_VALIDATE_NON_REGRESSIVE_TAX_BRACKETS,
    ) -> None:
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in Config.
        """
        self.market_rate_of_return: float = market_rate_of_return
        self.tax_brackets: MarketConfig.TaxBrackets = MarketConfig.TaxBrackets(
            tax_brackets["tax_brackets"], validate_non_regressive_tax_brackets
        )
        self.long_term_capital_gains_tax_brackets: MarketConfig.TaxBrackets = (
            MarketConfig.TaxBrackets(
                tax_brackets["long_term_capital_gains_tax_brackets"],
                validate_non_regressive_tax_brackets,
            )
        )
        self._validate()

    def _validate(self) -> None:
        """Sanity checks the configs.

        Raises:
            AssertionError: If any market configs are invalid
        """
        assert math.isfinite(
            self.market_rate_of_return
        ), "Market rate of return must not be NaN, infinity, or negative infinity."
        assert (
            self.market_rate_of_return <= MarketConfig.MAX_MARKET_RATE_OF_RETURN
        ), "Please set a reasonable market rate of return (at most 0.5)"
        assert self.tax_brackets is not None, "Tax brackets must not be null or empty."
        assert (
            self.long_term_capital_gains_tax_brackets is not None
        ), "long_term_capital_gains_tax_brackets must not be null or empty"

    def get_income_tax(self, income: float, deduction: float = 0) -> float:
        """Calculates tax owed given income.

        Args:
            income: non-negative income

        Returns:
            tax: non-negative tax owed
        """
        assert income >= 0, "Income must be non-negative"
        assert deduction >= 0, "Deduction must be non-negative"
        return self.tax_brackets._get_income_tax(income, deduction)

    def get_marginal_income_tax_rate(self, income) -> float:
        assert income >= 0
        return self.tax_brackets._get_marginal_income_tax_rate(income)

    def get_income_tax_savings_from_deduction(
        self, income: float, deduction: float
    ) -> float:
        """Calculates income tax savings due to deduction at the given original income.

        Args:
            income: non-negative income

        Returns:
            tax: non-negative tax owed
        """
        assert income >= 0, "Income must be non-negative"
        assert deduction >= 0, "Deduction must be non-negative"
        original_income_tax = self.get_income_tax(income)
        modified_income_tax = self.get_income_tax(income, deduction)
        return original_income_tax - modified_income_tax

    def get_pretax_monthly_wealth(self, principal: float, num_months: int) -> float:
        """Return the pretax wealth in the market at the BEGINNING of each month
        for num_months months.

        Wealth refers to the total amount of money in the market, not the
        return (which refers to just the difference in wealth between one month
        and the previous month).

        NOTE: The annual rate of return is given by the configs. To make some
        calculations easier, an "equivalent" monthly rate of return is
        calculated such that compounding the monthly rate every month results
        in an annual growth of the given annual rate of return. Thus,
        compounding the monthly rate every month for 24 months is also
        equivalent to compounding the annual rate every year for 2 years.

        Math equations:
            Let a = annual rate of return, compounded annually
            Let m = "equivalent" monthly rate of return, compounded monthly
            We are given a and want to find m
            After one year, principal grows to:
                If compounding annually: (1 + a) * principal
                If compounding monthly: (1 + m)**12 * principal
            They should be equal:
                (1 + a) * principal = (1 + m)**12 * principal
                (1 + a) = (1 + m)**12
                (1 + a)**(1/12) = 1 + m
                m = (1 + a)**(1/12) - 1
            E.g., if the annual rate of return compounded annually is 0.12
            (12%), the monthly rate of return compounded monthly is
            0.00948879293.

        Returns:
            list[float]: monthly wealth in dollars at th beginning of each month
                rounded to two decimal points.

        Raises:
            AssertionError: If the principal is negative or num_months is not positive
        """
        assert principal >= 0, "Principal invested must be non-negative."
        return math_utils.project_growth(
            principal=principal,
            annual_growth_rate=self.market_rate_of_return,
            compound_monthly=True,
            num_months=num_months,
        )
