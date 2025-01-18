# rent_buy_invest

## Overview

Calculates the long-term financial pros and cons of decisions related to renting a home, buying a home, and investing in the stock market.

This is a tool for helping determine whether to rent vs buy a home. The main financial parameters of the scenario must be specified in config files. The documentation on these config files are present in .md files in `rent_buy_invest/configs/schemas/`.

Some additional notes about the configs:
- You can set the start date to any time, but this calculator is not meant to indicate that the results here would match what happened historically. This calculator is just a limited approximator using the customs/laws as of around 2024/2025.
- There is a mortgage interest tax deduction. To get this deduction, you need to itemize your deductions instead of taking the standard deduction. This script assumes you will itemize your deductions. Although deductions are calculated annually, for convenience sake, it's done monthly in these calculations.
    - See IRS 2024 Publication 936 for details
- Typically, discount points which are paid upfront to reduce the interest rate on the mortgage can also be deducted from taxes. There are some finer details, but by and large, you can deduct discount points from your taxes if they are computed as a fraction of the principal balance and appear clearly as points on your settlement. Discount point payments are often thought of as some kind of prepaid interest. In this calculator, any deduction savings are accounted for in the initial state.
- Mortgage insurance used to be tax deductible, but it seems it no longer is.
- Property tax: Property taxes are billed annually based on the assessed value of the home. For convenience / to make the math easy, `rent_buy_invest` assumes this annual billing cycle start coincides with the start of the mortgage term.
- Homeowners insurance: Homeowners insurance pricing is based on the replacement cost of the home (the cost of rebuilding the home if it gets destroyed), plus the regular supply+demand of the market. Since replacement cost has to do with constructing the home and not the market value, it is put under the inflation-related home ownership costs, not the home value related home ownership costs.
- Depending on your situation, you may be required (by the lender, as a condition to getting a loan).
    - There are a few ways to pay mortgage insurance.
        - Monthly premium: You pay every month.
        - Upfront premium: You pay once upfront.
        - Split premium: You pay some portion upfront and some portion premium
        - Lender-paid premium: The lender pays the mortgage insurance. In exchange, they'll likely charge you a higher interest rate than otherwise.
    - `rent_buy_invest` does not yet include all these options. Ideally, it would include these options in the future. Currently, it is expected that the premium is paid monthly.
    - I think the monthly premium is the way to go, due to the fact that if you pay upfront, then you may not get a refund if you sell or refinance the home before the mortgage ends.
- "Prepaid expenses" is a category of expenses paid by a home buyer around the time of closing that are payments for upcoming expenses. These are not closing costs, though they are paid at the same/similar time. Prepaid expenses include a variety of different expenses. This tool does not handle prepaid expenses, and below is a description of each of the major types of prepaid expenses and why `rent_buy_invest` does NOT handle them:
    - Prepaid mortgage interest: Typically, mortgage payments are charged on the first of each month. So if you start your loan on a day besides the first, there is accumulated interest between when the loan starts and the first of the upcoming month. This amount is typically paid upfront as a prepaid expense. To make the calculations simpler, `rent_buy_invest` does not include this. You can enter a start date as on the first of a month. It should not really affect the rent vs buy comparison anyways - it seems to be a matter of accounting and payment schedule, not a matter of a change in amounts owed.
    - Prepaid homeowners insurance: You prepay homeowners insurance for some upcoming period of time, likely for the rest of the calendar year, or for the next 365 days, or for some set number of months. Also, it seems that you still pay periodically for homeowners insurance during the time where you're already covered, as forced prepayment for the next period. E.g., you may have a prepaid homeowners insurance for the first year, and during the first year, you pay ahead of time for the second year, and so on. It does seem like if you sell your home, you get the unused part back. To make the calculations simpler, `rent_buy_invest` does not include prepaid homeowners insurance. It should not really affect the rent vs buy comparison anyways - it seems to be a matter of accounting and payment schedule, not a matter of a change in amounts owed.
    - Prepaid property tax: Similarly, you may prepay some amount of future property tax. To make the calculations simpler, `rent_buy_invest` does not include prepaid homeowners insurance. It should not really affect the rent vs buy comparison anyways - it seems to be a matter of accounting and payment schedule, not a matter of a change in amounts owed.
    - Prepaid mortgage insurance: This is the upfront part of the mortgage insurance. This may be 0. Ideally, `rent_buy_invest` would handle this, but as of now it does not.
- Rental cost inflation: Currently, the `annual_rent_inflation_rate` is applied to all rental expenses, not just rent (e.g., rent, utilities, renter's insruance, etc.). Ideally `rent_buy_invest` would have separate inflation rates for different categories.
- Home cost inflation: There are a few different categories of costs associated with buying a home:
    - Home value related costs: property tax, homeowners insurance, maintenance, and management. These change according to `annual_assessed_value_inflation_rate`
    - Inflation related costs: utilities and HOA fees. These increase change according to `annual_inflation_rate`
    - Mortgage insurance: Mortgage insurance is calculated based on the initial loan amount
    - Mortgage interest: The interest portion of the mortgage payment. Since the mortgage payment is a constant value, and since the loan amount decreases over time, there is some math you can work out to show that the interest portion of the mortgage payment decreases over time according to some fixed schedule.

## Installation & How to Run

### Setup
- NOTE: You can (and probably should) do all of the following in a python virtual environment, e.g., using `venv`, but the instructions for doing so are not listed here (for now)
- Clone this repo
- Make sure you have python 3.11.4+ (anything 3.8+ should probably work) and pip3 installed
- Navigate to the 'rent_buy_invest' directory and run `pip3 install -r requirements.txt`
- To your `PYTHONPATH` environment variable, add the path to this repo

### Run the Code
Navigate to the directory containing `rent_buy_invest` and run:
`python3 rent_buy_invest/main.py rent_buy_invest/configs/examples/experiment-config-example-1.yaml`

## For Developers

### Making a PR
Steps:
- Before finalizing the PR, and ideally before every commit, from the `rent_buy_invest` folder, run `black .`, `isort .`, and for each of the four config files run `jsonschema2md path/to/<config_file>.json path/to/<config_file>.md`. Also make sure tests pass by running `pytest .`
- You can set at least some of this stuff up in a pre-commit hook, but I haven't done that yet.

### Updating the config schema
Steps:
- Update json schema (add/remove/modify the field in the appropriate .json file in `rent_buy_invest/configs/schemas/`). Remove to update the list of `required` fields appropriately.
- Update the config schema documentation: `jsonschema2md path/to/<config_file>.json path/to/<config_file>.md`
- Update the yaml config files, both examples and tests
    - examples are in `rent_buy_invest/configs/examples`
    - tests are in `rent_buy_invest/core/test_resources`
- Update appropriate config classes (the following classes in `rent_buy_invest/core/`: `experiment_config.py`, `rent_config.py`, `market_config.py`, `buy_config.py`)
- Update tests, both invalid_schema and invalid_inputs methods in the relevant test file
- Make sure all tests pass
- Make sure you can run the code
