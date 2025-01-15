# Personal Configuration

*Config file relating to assumptions about the person making the rent vs buy decision.*

## Properties

- **`income`** *(number, required)*: ANNUAL income. Income is used only for tax implications, not for determination of affordability.
- **`income_growth_rate`** *(number, required)*: ANNUAL rate of growth of income.
- **`years_till_retirement`** *(number, required)*: Number of years till retirement. After this many years, the income will reduce to 0. In reality, due to return on assets, government programs, etc., it should be more, but we ignore this for now.
