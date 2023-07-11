
def project_growth(principal: float, annual_growth_rate: float, num_months: int, round_to_cent: bool = True) -> float:
	"""Given a principal (starting amount) and an annual growth rate, return
	the value each month for num_months months.

	Returns:
		List[float]: monthly value in dollars

	Raises:
		AssertionError: If principal is negative or num_months is not positive
	"""
	assert principal >= 0
	assert num_months > 0
	monthly_values = []
	for month in range(num_months):
		monthly_value = principal * (1+annual_growth_rate)**(month // 12)
		if round_to_cent:
			monthly_value = round(monthly_value, 2)
		monthly_values.append(monthly_value)
	return monthly_values