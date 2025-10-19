# Personal Configuration

*Config file relating to assumptions about the person making the rent vs buy decision.*

## Properties

- **`ordinary_income`** *(number, required)*: ANNUAL ordinary (earned) income (e.g., income reported on a W-2 from employers). Oncome is used only for tax implications, not for determination of affordability.
- **`ordinary_income_growth_rate`** *(number, required)*: ANNUAL rate of growth of ordinary income.
- **`years_till_retirement`** *(number, required)*: Number of years till retirement. After this many years, the ordinary income will reduce to 0. In reality, due to return on assets, government programs, etc., it should be more, but we ignore this for now.
