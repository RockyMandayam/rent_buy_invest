# Market Configuration

*Config file relating to assumptions about the 'market'.*

## Properties

- **`market_rate_of_return`** *(number, required)*: ANNUAL rate of return in the market, as a fraction.
- **`tax_brackets`** *(object, required)*: Tax brackets.
  - **`ordinary_income_tax_brackets`** *(array, required)*: Income tax (also short term capital gains tax) brackets. List of tax brackets ordered from lowest bracket to highest bracket. Each bracket has a lower limit, upper limit, and marginal tax rate. The first bracket's lower limit is assumed to be 0, and every other bracket's lower limit is equal to its previous bracket's upper limit. The last bracket's upper limit must be infinity.
    - **Items** *(object)*
      - **`upper_limit`** *(number, required)*: The upper limit of this tax bracket.
      - **`tax_rate`** *(number, required)*: The marginal tax rate for this tax bracket.
  - **`long_term_capital_gains_tax_brackets`** *(array, required)*: Long term capital gains tax brackets. List of tax brackets ordered from lowest bracket to highest bracket. Each bracket has a lower limit, upper limit, and marginal tax rate. The first bracket's lower limit is assumed to be 0, and every other bracket's lower limit is equal to its previous bracket's upper limit. The last bracket's upper limit must be infinity.
    - **Items** *(object)*
      - **`upper_limit`** *(number, required)*: The upper limit of this tax bracket.
      - **`tax_rate`** *(number, required)*: The marginal tax rate for this tax bracket.
