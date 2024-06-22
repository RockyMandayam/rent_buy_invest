# rent-buy-invest
Calculates the long-term financial pros and cons of decisions related to renting a home, buying a house, and investing in the stock market.

## Getting Started (Users)

### Setup
- NOTE: You can (and probably should) do all of the following in a python virtual environment, e.g., using `venv`, but the instructions for doing so are not listed here (for now)
- Clone this repo
- Make sure you have python 3.11.4+ (anything 3.8+ should probably work) and pip3 installed
- Navigate to the top-level directory of this repo and run `pip3 install -r requirements.txt`
- To your `PYTHONPATH` environment variable, add the path to this repo

### Run the Code
Navigate to the directory containing `rent_buy_invest` and run:
`python3 rent_buy_invest/main.py rent_buy_invest/configs/examples/experiment-config-example-1.yaml`

## Getting Started (Developers)

### Adding fields to configs
Steps:
- Update json schema (add the field and also make it required if required)
- Add the field to all configs, both examples and tests
- Update appropriate config class
- Update tests, both invalid_schema and invalid_inputs methods in the relevant test file
- Make sure all tests pass
- Make sure you can run the code
