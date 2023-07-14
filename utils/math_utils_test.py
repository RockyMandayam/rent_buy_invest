from . import math_utils

def test_get_monthly_costs() -> None:
	# TODO test all parameters
	principal = 1000
	annual_inflation_rate = 0.03
	num_months = 25

	actual = math_utils.project_growth(principal, annual_inflation_rate, False, num_months)
	expected = [principal]*12 + [round(principal * 1.03, 2)]*12 + [round(principal * 1.03**2, 2)]
	assert actual == expected
