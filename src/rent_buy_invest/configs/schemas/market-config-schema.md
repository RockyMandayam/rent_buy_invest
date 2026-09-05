# Market Configuration

*Config file relating to assumptions about the 'market'.*

## Properties

- **`market_rate_of_return`** *(number, required)*: ANNUAL rate of return in the market, as a fraction.
- **`market_dividend_yield`** *(number, required)*: The part of 'market_rate_of_return' that arrives each year as taxable dividends, as a fraction of the account balance (0.013 is close to the S&P 500's recent yield). It is a slice OF the total return, not an addition to it: price appreciation is 'market_rate_of_return' minus this, so raising it moves return out of untaxed growth and into income taxed every year, rather than making the account grow faster. Set it to 0 to treat the whole return as appreciation, taxed only when the account is sold. Dividends are assumed to be 100% qualified and reinvested, so they are taxed at the long-term capital gains brackets and stay in the account. That fits a broad stock index fund; it is too generous for REITs, bond funds, and many foreign funds, whose distributions are largely taxed as ordinary income. NOTE: this only affects the 'rental_vs_invest' mode today; the 'rent_vs_buy' projection does not model dividend tax at all, so setting this has no effect there.
- **`tax_brackets_inflation`** *(number, required)*: Rate at which the tax bracket limits inflate (by government policy).
- **`annual_inflation_rate`** *(number, required)*: General ANNUAL rate of price inflation in the economy, as a fraction. Used to grow the home costs that track prices rather than home value: utilities, HOA fees, homeowners and flood insurance, and the home warranty. This is not the rate rents rise at, which is 'annual_rent_inflation_rate' in the rent config, and it is not the rate home values rise at, which is 'annual_home_appreciation_rate' in the buy config.
- **`tax_brackets`** *(object, required)*: Tax brackets.
  - **`ordinary_income_tax_brackets`** *(array, required)*: Ordinary income tax (also short term capital gains tax) brackets. List of tax brackets ordered from lowest bracket to highest bracket. Each bracket has a lower limit, upper limit, and marginal tax rate. The first bracket's lower limit is assumed to be 0, and every other bracket's lower limit is equal to its previous bracket's upper limit. The last bracket's upper limit must be infinity.
    - **Items** *(object)*
      - **`upper_limit`** *(number, required)*: The upper limit of this tax bracket.
      - **`tax_rate`** *(number, required)*: The marginal tax rate for this tax bracket.
  - **`long_term_capital_gains_tax_brackets`** *(array, required)*: Long term capital gains tax brackets. List of tax brackets ordered from lowest bracket to highest bracket. Each bracket has a lower limit, upper limit, and marginal tax rate. The first bracket's lower limit is assumed to be 0, and every other bracket's lower limit is equal to its previous bracket's upper limit. The last bracket's upper limit must be infinity.
    - **Items** *(object)*
      - **`upper_limit`** *(number, required)*: The upper limit of this tax bracket.
      - **`tax_rate`** *(number, required)*: The marginal tax rate for this tax bracket.
