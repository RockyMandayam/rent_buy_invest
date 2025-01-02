# House Configuration

*Config file relating to assumptions about buying, owning, and selling a house.*

## Properties

- **`sale_price`** *(number, required)*: Sale price of the house (final nominal sale price).
- **`annual_assessed_value_inflation_rate`** *(number, required)*: ANNUAL inflation rate of house assessed value as a fraction.
- **`down_payment_fraction`** *(number, required)*: The fraction of the house price put down as the down payment (the remaining is assumed to be the mortgage principal).
- **`mortgage_annual_interest_rate`** *(number, required)*: Mortgage ANNUAL interest rate. An 'equivalent' monthly interest rate can be calculated from this. Note that the equivalent monthly interest rate is not just 1/12 of the annual rate, due to the fact that the monthly rate is compounded monthly (i.e., it is a compound interst rate not a simple interest rate).
- **`mortgage_term_months`** *(number, required)*: Mortgage term (length) in months.
- **`pmi_fraction`** *(number, required)*: Private mortgage insurance (PMI) cost as fraction of mortgage principal.
- **`mortgage_origination_points_fee_fraction`** *(number, required)*: Mortgage origination points (a.k.a. loan origination fee) are basically just a fee the lender charges for originating (creating), reviewing, processing, etc. the loan. This field is expressed as a fraction of the mortgage amount.
- **`mortgage_processing_fee`** *(number, required)*: Mortgage processing fee. Some lenders include this in the origination fee. Do NOT include that amount here. Only include here any amount not covered under other fees.
- **`mortgage_underwriting_fee`** *(number, required)*: Mortgage underwriting fee. Some lenders include this in the origination fee. Do NOT include that amount here. Only include here any amount not covered under other fees.
- **`mortgage_discount_points_fee_fraction`** *(number, required)*: Mortgage discount points (a.k.a. mortgage points) are a fee you can pay up-front to lower your mortgage interest rate. The FINAL mortgage interest rate should be given above (regardless of how that rate was gotten). If you used discount points to achieve that rate, that final rate should be given here as a fraction of the mortgage amount.
- **`house_appraisal_cost`** *(number, required)*: House appraisal cost. Lenders often require a house appraisal. The buyer often pays for this up-front, regardless of whether the sale actually goes through.
- **`credit_report_fee`** *(number, required)*: Credit report fee charged by lender to do a credit check.
- **`transfer_tax_fraction`** *(number, required)*: Transfer tax as a fraction of the sale price. Note that there are often multiple transfer taxes (e.g., state and county). This field is the sum of all such transfer taxes. Transfer tax is a one-time tax per house purchase.
- **`seller_burden_of_transfer_tax_fraction`** *(number, required)*: The fraction of the transfer tax burden is borne by the seller (the remaining is borne by the buyer).
- **`recording_fee_fraction`** *(number, required)*: The tax charged by the county/state/etc. to legally record the property's deed and mortgage information. This field is expressed as fraction of sale price. The recording fee is often considered part of the title fees and therefore part of the 'closing costs'.
- **`annual_property_tax_rate`** *(number, required)*: ANNUAL property tax rate (a fraction of the house's assessed value).
- **`realtor_commission_fraction`** *(number, required)*: The buyer's realtor's commission as a fraction of sale price.
- **`hoa_transfer_fee`** *(number, required)*: The fee to sell a home that is part of an HOA (Home Owners Association).
- **`seller_burden_of_hoa_transfer_fee`** *(number, required)*: The seller's burden of the HOA transfer fee as a fraction of the fee.
- **`house_inspection_cost`** *(number, required)*: The house inspection cost. The house inspection should include at least the following types: general, foundation, plumbing, septic tank, termite, mold, and chimney. Typically a house inspection does NOT include a pest inspection.
- **`pest_inspection_cost`** *(number, required)*: The pest inspection cost (note that the house inspection probably does not include pest inspection).
- **`escrow_fixed_fee`** *(number, required)*: Escrow fixed fee. I don't think there is a basic price-based fee except for specific line items, e.g., flood certification fee.
- **`flood_certification_fee`** *(number, required)*: Flood certification fee.
- **`title_search_fee`** *(number, required)*: Title search fee.
- **`seller_burden_of_title_search_fee_fraction`** *(number, required)*: The seller's burden of the title search fee as a fraction.
- **`attorney_fee`** *(number, required)*: Attorney fee.
- **`closing_protection_letter_fee`** *(number, required)*: The closing protection letter (CPL) fee.
- **`search_abstract_fee`** *(number, required)*: Search abstract fee. This may be included in the title search fee. Do NOT include that amount here. Only include here any amount not covered under other fees. This is often loosely considered part of 'title fees' or 'settlement fees'.
- **`survey_fee`** *(number, required)*: Survey fee, which surveys the boundaries of the property. This is often loosely considered part of 'settlement fees'.
- **`notary_fee`** *(number, required)*: Notary fee. This is often loosely considered part of 'settlement fees'.
- **`deed_prep_fee`** *(number, required)*: Deed preparation fee. This is often loosely considered part of 'settlement fees'.
- **`lenders_title_insurance_fraction`** *(number, required)*: Lender's title insurance (which protects the lender) as a fraction of the mortgage amount. Apparently there is a wide range of typical values here.
- **`owners_title_insurance_fraction`** *(number, required)*: Owner's title insurance (which protects the owner (you!)) as a fraction of the mortgage amount. Apparently there is a wide range of typical values here.
- **`endorsement_fees`** *(number, required)*: Endorsement fees are for add-ons ('endorsements') that are not included in a standard title insurance (e.g., Easements And Encroachments, Zoning). A typical price per-endorsement is about $75. Enter the total amount you expect for all endorsements.
- **`annual_homeowners_insurance_fraction`** *(number, required)*: ANNUAL cost of homeowners insurance as fraction of the assessed house value. This field depends a lot on the house, conditions, coverage, insurance, etc.
- **`monthly_utilities`** *(number, required)*: Monthly utilities for the first month.
- **`annual_maintenance_cost_fraction`** *(number, required)*: ANNUAL maintenance cost as a fraction of the assessed house value (not sale price).
- **`monthly_hoa_fees`** *(number, required)*: Monthly HOA (Home Owners Association) fees.
- **`annual_management_cost_fraction`** *(number, required)*: Total ANNUAL cost of managing the house (expressed as a fraction of assessed house price) without living in it (i.e., being a landlord but not a resident), EXCEPT for maintenance costs that you'd expect to pay even if you lived in the house. Note that this means if you expect maintenance costs to be higher when you do not live in the house vs when you live in it (because you think tenants will take worse care of the house than you would if you lived in t), that difference in cost should contribute to this parameter. Note this parameter can include paying a management company, advertising the house, any trips you may have to make, anything associated with managing / landlord.
