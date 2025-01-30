import math

from rent_buy_invest.configs.config import Config
from rent_buy_invest.utils import math_utils

DEFAULT_VALIDATE_NON_REGRESSIVE_TAX_BRACKETS = True


class MarketConfig(Config):
    """Stores market config.

    Class attributes:
        schema_path (str): Market config schema path

    Instance Attributes:
        self.market_rate_of_return: ANNUAL rate of return in the market, as a decimal
        self.tax_brackets_inflation: Rate at which the tax bracket limits inflate (by government policy)
        # TODO more tax stuff (e.g., standard exemption, net investment income tax, payroll tax, etc.)
        self.ordinary_income_tax_brackets: A TaxBrackets object representing ordinary income tax rates (which are also the tax rates used for short term capital gains and some other types of unearned income)
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
                is the upper limit of that bracket (beyond that limit, the
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

        def get_inflated(self, inflation_factor: float) -> "MarketConfig.TaxBrackets":
            inflated_tax_brackets = [
                {
                    "upper_limit": bracket["upper_limit"] * inflation_factor,
                    "tax_rate": bracket["tax_rate"],
                }
                for bracket in self.tax_brackets
            ]
            return MarketConfig.TaxBrackets(
                tax_brackets=inflated_tax_brackets,
                validate_non_regressive_tax_brackets=self.validate_non_regressive_tax_brackets,
            )

        def _get_tax(self, income: float, offset: float = 0) -> float:
            """Calculates tax owed given income.

            Args:
                income: non-negative income
                offset: an offset to "start calculating" from
                    - Usefor for calculating one tax "on top of" another (e.g., capital gains on top of income)
                    - The way the income tax and the capital gains tax work is:
                        - First calculate the income tax as normal using the income tax brackets
                        - Then, using the income as the "offset", add the capital gains amount from that offset to the capital gains tax brackets
                        - E.g.:
                            - Suppose you have $100k income and $20k capital gains tax
                            - Suppose the tax brackets are:
                                - Income tax: 10% up to $50k, 20% for the rest
                                - Capital gains tax: 0% up to $10k, 5% for the rest
                            - Income = $100k = $50k + $50k. Income tax is 10% of $50k plus 20% of $50k = 0.1*50k + 0.2*50k = 15k
                            - Capital gains = $20k = $10k + $10k. Capital gains tax STARTS at the 100k, so you pay 5% for $20k (the 100k to 120k range basically)

            Returns:
                tax: non-negative tax owed
            """
            # this is the range that is taxed
            taxable_range_lower_limit = offset
            taxable_range_upper_limit = offset + income

            # iterate through brackets and add up taxes owed on each bracket
            tax = 0
            bracket_lower_limit = 0
            for bracket in self.tax_brackets:
                bracket_upper_limit = bracket["upper_limit"]
                # skip if bracket is below taxable range
                if bracket_upper_limit < taxable_range_lower_limit:
                    continue
                # stop if bracket is fully above taxable range
                if taxable_range_upper_limit < bracket_lower_limit:
                    break
                tax_rate = bracket["tax_rate"]
                # if bracket covers the top and end of taxable range, calculate fractional tax on that last portion and end
                if taxable_range_upper_limit <= bracket_upper_limit:
                    tax += tax_rate * (
                        taxable_range_upper_limit - max(bracket_lower_limit, offset)
                    )
                    break
                # otherwise, add up tax for this bracket, potentially startinot not at the lower limit due to the offset
                tax += tax_rate * (
                    bracket_upper_limit
                    - max(bracket_lower_limit, taxable_range_lower_limit)
                )
                bracket_lower_limit = bracket_upper_limit
            return tax

    def __init__(
        self,
        market_rate_of_return: float,
        tax_brackets_inflation: float,
        tax_brackets: dict[str, dict],
        validate_non_regressive_tax_brackets: bool = DEFAULT_VALIDATE_NON_REGRESSIVE_TAX_BRACKETS,
    ) -> None:
        """Initializes the class.

        To see why I don't use yaml tags, see the docstring for __init__
        in Config.
        """
        self.market_rate_of_return: float = market_rate_of_return
        self.tax_brackets_inflation: float = tax_brackets_inflation
        self.ordinary_income_tax_brackets: MarketConfig.TaxBrackets = (
            MarketConfig.TaxBrackets(
                tax_brackets["ordinary_income_tax_brackets"],
                validate_non_regressive_tax_brackets,
            )
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
        assert math.isfinite(
            self.tax_brackets_inflation
        ), "tax_brackets_inflation must not be NaN, infinity, or negative infinity"
        assert (
            self.tax_brackets_inflation >= 0
        ), "tax_brackets_inflation must be non-negative."
        assert (
            self.market_rate_of_return <= MarketConfig.MAX_MARKET_RATE_OF_RETURN
        ), "Please set a reasonable market rate of return (at most 0.5)"
        assert (
            self.ordinary_income_tax_brackets is not None
        ), "Ordinary income tax brackets must not be null or empty."
        assert (
            self.long_term_capital_gains_tax_brackets is not None
        ), "long_term_capital_gains_tax_brackets must not be null or empty"

    def get_tax(
        self,
        month: int,
        ordinary_income: float,
        ordinary_income_deduction: float = 0,
        long_term_capital_gains: float = 0,
        long_term_capital_gains_deduction: float = 0,
    ) -> float:
        """Calculates tax owed given income.

        Args:
            ordinary_income: non-negative ordinary_income

        Returns:
            tax: non-negative tax owed
        """
        assert month >= 0, "Month must be non-negative"
        assert ordinary_income >= 0, "Ordinary income must be non-negative"
        assert (
            ordinary_income_deduction >= 0
        ), "Ordinary income deduction must be non-negative"
        assert long_term_capital_gains >= 0, "Capital gains must be non-negative"
        assert (
            long_term_capital_gains_deduction >= 0
        ), "Capital gains deduction must be non-negative"
        # subtract deductions - cannot deduct more than income
        ordinary_income_deduction = min(ordinary_income_deduction, ordinary_income)
        ordinary_income -= ordinary_income_deduction
        long_term_capital_gains_deduction = min(
            long_term_capital_gains_deduction, long_term_capital_gains
        )
        long_term_capital_gains -= long_term_capital_gains_deduction
        # get current tax brackets (inflated yearly)
        year = month // math_utils.MONTHS_PER_YEAR
        inflation_factor = (1 + self.tax_brackets_inflation) ** year
        current_ordinary_income_tax_brackets = (
            self.ordinary_income_tax_brackets.get_inflated(inflation_factor)
        )
        current_long_term_capital_gains_tax_brackets = (
            self.long_term_capital_gains_tax_brackets.get_inflated(inflation_factor)
        )
        # calculate taxes
        ordinary_income_tax = current_ordinary_income_tax_brackets._get_tax(
            ordinary_income
        )
        long_term_capital_gains_tax = (
            current_long_term_capital_gains_tax_brackets._get_tax(
                long_term_capital_gains, ordinary_income
            )
        )
        return ordinary_income_tax + long_term_capital_gains_tax

    def get_additional_tax_from_additional_income(
        self, month: int, base_ordinary_income: float, additional_ordinary_income: float
    ) -> float:
        assert month >= 0, "Month must be non-negative"
        assert base_ordinary_income >= 0, "Base ordinary income must be non-negative"
        assert (
            additional_ordinary_income >= 0
        ), "Additional ordinary income must be non-negative"
        base_tax = self.get_tax(month, base_ordinary_income)
        tax_with_additional_income = self.get_tax(
            month, base_ordinary_income + additional_ordinary_income
        )
        # TODO just noticed here that values are not rounded...
        return tax_with_additional_income - base_tax

    def get_income_tax_savings_from_deduction(
        self, month: int, income: float, deduction: float
    ) -> float:
        """Calculates income tax savings due to deduction at the given original income.

        Args:
            income: non-negative income

        Returns:
            tax: non-negative tax owed
        """
        assert month >= 0, "Month must be non-negative"
        assert income >= 0, "Income must be non-negative"
        assert deduction >= 0, "Deduction must be non-negative"
        original_income_tax = self.get_tax(month, income)
        modified_income_tax = self.get_tax(month, income, deduction)
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
        assert num_months > 0
        assert principal >= 0, "Principal invested must be non-negative."
        return math_utils.project_growth(
            principal=principal,
            annual_growth_rate=self.market_rate_of_return,
            compound_monthly=True,
            num_months=num_months,
        )
