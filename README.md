# rent_buy_invest

## Overview

Calculates the long-term financial pros and cons of decisions related to renting a home, buying a house, and investing in the stock market.

This is a tool for helping determine whether to rent vs buy a home. The main financial parameters of the scenario must be specified in config files. The documentation on these config files are present in .md files in `rent_buy_invest/configs/schemas/`.

Some additional notes about the configs:
- Depending on your situation, you may be required (by the lender, as a condition to getting a loan).
    - There are a few ways to pay PMI.
        - Monthly premium: You pay every month.
        - Upfront premium: You pay once upfront.
        - Split premium: You pay some portion upfront and some portion premium
        - Lender-paid premium: The lender pays the PMI. In exchange, they'll likely charge you a higher interest rate than otherwise.
    - `rent_buy_invest` does not yet include all these options. Ideally, it would include these options in the future. Currently, it is expected that the premium is paid monthly.
- "Prepaid expenses" is a category of expenses paid by a home buyer around the time of closing that are payments for upcoming expenses. These are not closing costs, though they are paid at the same/similar time. Prepaid expenses include a variety of different expenses. This tool does not handle prepaid expenses, and below is a description of each of the major types of prepaid expenses and why `rent_buy_invest` does NOT handle them:
    - Prepaid mortgage interest: Typically, mortgage payments are charged on the first of each month. So if you start your loan on a day besides the first, there is accumulated interest between when the loan starts and the first of the upcoming month. This amount is typically paid upfront as a prepaid expense. To make the calculations simpler, `rent_buy_invest` does not include this. You can enter a start date as on the first of a month. It should not really affect the rent vs buy comparison anyways - it seems to be a matter of accounting and payment schedule, not a matter of a change in amounts owed.
    - Prepaid homeowners insurance: You prepay homeowners insurance for some upcoming period of time, likely for the rest of the calendar year, or for the next 365 days, or for some set number of months. Also, it seems that you still pay periodically for homeowners insurance during the time where you're already covered, as forced prepayment for the next period. E.g., you may have a prepaid homeowners insurance for the first year, and during the first year, you pay ahead of time for the second year, and so on. It does seem like if you sell your home, you get the unused part back. To make the calculations simpler, `rent_buy_invest` does not include prepaid homeowners insurance. It should not really affect the rent vs buy comparison anyways - it seems to be a matter of accounting and payment schedule, not a matter of a change in amounts owed.
    - Prepaid property tax: Similarly, you may prepay some amount of future property tax. To make the calculations simpler, `rent_buy_invest` does not include prepaid homeowners insurance. It should not really affect the rent vs buy comparison anyways - it seems to be a matter of accounting and payment schedule, not a matter of a change in amounts owed.
    - Prepaid mortgage insurance: This is the upfront part of the mortgage insurance. This may be 0. Ideally, `rent_buy_invest` would handle this, but as of now it does not.

## Installation & How to Run

### Setup
- NOTE: You can (and probably should) do all of the following in a python virtual environment, e.g., using `venv`, but the instructions for doing so are not listed here (for now)
- Clone this repo
- Make sure you have python 3.11.4+ (anything 3.8+ should probably work) and pip3 installed
- Navigate to the top-level directory of this repo and run `pip3 install -r requirements.txt`
- To your `PYTHONPATH` environment variable, add the path to this repo

### Run the Code
Navigate to the directory containing `rent_buy_invest` and run:
`python3 rent_buy_invest/main.py rent_buy_invest/configs/examples/experiment-config-example-1.yaml`

## For Developers

### Updating the config schema
Steps:
- Update json schema (add/remove/modify the field in the appropriate .json file in `rent_buy_invest/configs/schemas/`). Remove to update the list of `required` fields appropriately.
- Update the config schema documentation: `jsonschema2md path/to/<config_file>.json path/to/<config_file>.md`
- Update the yaml config files, both examples and tests
    - examples are in `rent_buy_invest/configs/examples`
    - tests are in `rent_buy_invest/core/test_resources`
- Update appropriate config classes (the following classes in `rent_buy_invest/core/`: `experiment_config.py`, `rent_config.py`, `market_config.py`, `house_config.py`)
- Update tests, both invalid_schema and invalid_inputs methods in the relevant test file
- Make sure all tests pass
- Make sure you can run the code
