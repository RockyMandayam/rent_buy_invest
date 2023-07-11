from . import math_utils

def test_get_monthly_costs() -> None:
	# TODO test not rounding
	first_monthly_cost = 1000
	annual_inflation_rate = 0.12
	num_months = 25

	actual = math_utils.get_monthly_costs(first_monthly_cost, annual_inflation_rate, num_months)
	expected = [first_monthly_cost]*12 + [round(first_monthly_cost * 1.03, 2)]*12 + [round(first_monthly_cost * 1.03**2, 2)]
	assert actual == expected
