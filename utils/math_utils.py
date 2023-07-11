
def get_monthly_costs(first_monthly_cost: float, annual_inflation_rate: float, num_months: int, round_to_cent: bool = True) -> float:
	"""Return the monthly cost each month for num_months months given the first
	month's cost and an inflation rate.

	Returns:
		List[float]: monthly cost of renting in dollars rounded to two
			decimal points.

	Raises:
		AssertionError: If first_monthly_cost is negative or num_months is not positive
	"""
	assert first_monthly_cost >= 0
	assert num_months > 0
	monthly_costs = []
	for month in range(num_months):
		monthly_cost = first_monthly_cost * (1+annual_inflation_rate)**(month // 12)
		if round_to_cent:
			monthly_cost = round(monthly_cost, 2)
		monthly_costs.append(monthly_cost)
	return monthly_costs