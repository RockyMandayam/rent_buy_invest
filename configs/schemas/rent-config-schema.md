# Rent Configuration

*Config file relating to assumptions about rent.*

## Properties

- **`monthly_rent`** *(number, required)*: Monthly rent for the first month.
- **`monthly_utilities`** *(number, required)*: Monthly utilities for the first month.
- **`monthly_renters_insurance`** *(number, required)*: Monthly renters insurance for the first month.
- **`monthly_parking_fee`** *(number, required)*: Monthly parking fee for the first month.
- **`annual_rent_inflation_rate`** *(number, required)*: ANNUAL rent inflation rate as a fraction. This will be applied to all expenses, not just rent (e.g., rent, utilities, renter's insurance, etc.).
- **`inflation_adjustment_period`** *(number, required)*: How often, in months, to update expenses due to inflation. Twelve is a good number here, as leases are often for 12-month periods and rents change when leases end.
- **`security_deposit`** *(number, required)*: The security deposit (in dollars) which will be returned back to you minus expenses that the landowner charges for cleaning, damages, etc.
- **`unrecoverable_fraction_of_security_deposit`** *(number, required)*: The fraction of the security deposit that you expect NOT to be returned to you ever.
