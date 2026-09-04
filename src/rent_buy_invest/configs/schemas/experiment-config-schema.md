# Experiment Configuration

*Configuration for one 'experiment'.*

## Properties

- **`mode`** *(string, required)*: Which comparison to run. 'rent_vs_buy' compares renting a home to live in against buying one to live in. 'rental_vs_invest' compares buying a property to rent out against putting the same money in the market; where you live does not appear in that comparison at all, because it is the same either way and cancels out. Both modes can be described by the same config files, so this states which question you are asking rather than being inferred from the data. Must be one of: `["rent_vs_buy", "rental_vs_invest"]`.
- **`num_years`** *(integer, required)*: The number of years to run the calculations for (max of 200).
- **`market_config_path`** *(string, required)*: Market config file path from the 'rent_buy_invest' directory.
- **`rent_config_path`** *(['string', 'null'], required)*: Rent config file path from the 'rent_buy_invest' directory. Required when mode is 'rent_vs_buy'. Must be null when mode is 'rental_vs_invest', which has no rent side at all -- supplying one there would be a file that changes nothing.
- **`buy_config_path`** *(string, required)*: Buy config file path from the 'rent_buy_invest' directory.
- **`personal_config_path`** *(string, required)*: Personal config file path from the 'rent_buy_invest' directory.
- **`start_date`**: Start date of the financial projection (the date when the home ownership is transferred to you).
