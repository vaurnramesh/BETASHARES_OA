# BETASHARES_OA

## How to Run 

```
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

python3 src/main.py

pytest -v
```

Outputs will be saved to:

`./data/output/output.csv` (detailed trades)

`./data/output/summary.json` (portfolio summary)


## Overview 

This project simulates the construction and rebalancing of a market-cap-weighted index portfolio. It calculates allocations, trades, and portfolio statistics over time in a structured and reproducible workflow.

The primary goals are:

1. Demonstrate portfolio construction using market-cap weighting.

2. Simulate rebalancing between dates.

3. Compute trades, allocations, and turnover.

4. Save both detailed trade logs (CSV) and high-level summaries (JSON) for reporting.


## Data Loading

Input is a CSV file with stock-level data:

| Column         | Description                       |
| -------------- | --------------------------------- |
| `date`         | Date of the stock price           |
| `company`      | Stock/company name                |
| `market_cap_m` | Market capitalization in millions |
| `price`        | Stock price                       |

## Index Creation

Input Table for example - 

| date       | company | market_cap_m | price |
|------------|---------|--------------|-------|
| 8/04/2025  | A       | 1200         | 12.32 |
| 8/04/2025  | B       | 800          | 4.52  |
| 8/04/2025  | C       | 4000         | 8.45  |


1. Filter stocks for the target date 
2. Sort by descending market capitalization 
3. Compute total market cap
4. Calculate weights

```
weight = market_cap / total_market_cap

```
5. Cumulative weights are calculated to apply a cutoff

    * `cumulative <= cutoff` -> include stock in the index (`universe_in`)
    * `cumulative > cutoff` -> exclude stock (`universe_out`)

6. Allocate Capital proportionally

```
allocation ​= capital × weight
```

7. Compute shares to buy

```
shares ​= allocation / price
```

Output Table - 

| Company | Market cap | Weight | Cumulative | Allocation | Shares |
| ------- | ---------- | ------ | ---------- | ---------- | ------ |
| A       | 1000       | 0.10   | 0.10       | 10,000,000 | 500    |
| B       | 900        | 0.09   | 0.19       | 9,000,000  | 300    |
| C       | 800        | 0.08   | 0.27       | 8,000,000  | 200    |


## Rebalancing: The Crux

When the portfolio is re-evaluated on a new date, we need to compare the old and new index universes

1. Define old and new universes:

| Universe           | Description                 |
| ------------------ | --------------------------- |
| `universe_in_old`  | Stocks included on old date |
| `universe_out_old` | Stocks excluded on old date |
| `universe_in_new`  | Stocks included on new date |
| `universe_out_new` | Stocks excluded on new date |


2. Determine stock actions using set operations (inner joins / differences):

| Set          | Logic               | Action        |
| ------------ | ------------------- | ------------- |
| `hold_set`   | `old_in & new_in`   | ADJUST shares |
| `sell_set`   | `old_in & new_out`  | SELL all      |
| `buy_set`    | `old_out & new_in`  | BUY new       |
| `ignore_set` | `old_out & new_out` | IGNORE        |



3. Calculate trades

**trade_shares**

Definition: The number of shares that need to be traded (bought or sold) to move from the old portfolio to the new portfolio.

Calculation:

| Action | Formula                                  | Meaning                                                              |
| ------ | ---------------------------------------- | -------------------------------------------------------------------- |
| ADJUST | `trade_shares = new_shares - old_shares` | Some shares already held, need to buy/sell extra to reach new target |
| BUY    | `trade_shares = new_shares - 0`          | Stock is new to the index → buy all required shares                  |
| SELL   | `trade_shares = 0 - old_shares`          | Stock is leaving index → sell all held shares                        |

> **Sign convention:**  
> Positive values indicate a **buy**. 
> Negative values indicate a **sell**.


**trade_value**

Definition: The dollar value of the trade for that stock.

```
trade_value = trade_shares * price
```

* For BUY trades, `trade_value = allocation` because all shares are new purchases
* For ADJUST and SELL, it’s calculated as `trade_shares * price`

| Stock | trade\_shares | price | trade\_value |
| ----- | ------------- | ----- | ------------ |
| A     | 20            | 12.32 | 246.40       |
| B     | -50           | 4.52  | -226.00      |
| C     | 80            | 8.45  | 676.00       |



> **Note on trade_value:**
> * For ADJUST, trade_value represents the incremental cash flow required (Δshares × price).
> * For BUY, trade_value equals the entire new allocation.
> * For SELL, trade_value equals the entire old allocation liquidated.
  This makes it easy to see the full capital rotation when stocks enter or leave the index, while incremental trades within the index are tracked separately.
> * Positive values indicate a **buy**. 
> * Negative values indicate a **sell**


## Portfolio Summary

After rebalancing the portfolio, we generate a summary report that tells us how the portfolio has changed and how much trading activity was required. This is critical for understanding the portfolio’s performance and cash flow.

1. Portfolio Values

    * **Old Portfolio Value**: The total market value of all stocks before rebalancing.

    * **New Portfolio Value**: The total market value of all stocks after rebalancing.

    * **Total Trade Value**: The sum of all trades (both buys and sells), giving a measure of how much trading was needed to achieve the new portfolio.

2. Trading Breakdown
    *  **Buy Value**: Dollar value spent on new equities added to the portfolio.
    * **Sell Value**: Dollar value received from equities removed from the portfolio.
    * **Adjust Value**: Dollar value of trades for stocks that remain in the portfolio but needed adjustments to reach their new target weights.

3. Turnover

    * **Turnover %**: Measures how much of the portfolio’s value was traded relative to the new portfolio value.
    * A high turnover indicates more active rebalancing, while a low turnover suggests minimal changes.
    * Turnover % is calculated as sum of absolute trade values divided by new portfolio value. Industry convention may use `min(BUY, SELL) ÷ avg(portfolio_value)`.

4. Equity Changes

    * **Total New Shares**: Total number of shares purchased for newly added stocks.
    * **Total Sold Shares**: Total number of shares sold for stocks removed from the portfolio.

5. Detailed Trade Lists

    * **New Buys Table**: Shows all newly added stocks, the number of shares purchased, and the dollar value spent.
    * **Sold Stocks Table:** Shows all stocks removed from the portfolio, the number of shares sold, and the dollar value received.





## Scenarios & Real World Considerations

### 1. Data Issues (Formatting / Content)

- **Missing values**  
  - `market_cap_m`, `price`, or `date` could be NULL, leading to divide-by-zero or NaN results.  
- **Incorrect data types**  
  - Market cap or price stored as strings instead of numeric.  
- **Duplicate rows**  
  - Same company and date repeated, inflating weights.  
- **Wrong or inconsistent date format**  
  - e.g. `2025-08-05` vs `08/05/2025`, causing filter mismatch.  
- **Outliers or bad inputs**  
  - Negative or zero prices (not realistic).  
  - Market cap = 0 or negative (corrupt data).  
- **Company identifier inconsistency**  
  - Company names misspelled or multiple tickers representing the same firm.  



### 2. Code Weaknesses

- **Division by zero**  
  - If total market cap = 0, weights calculation fails.  
- **Empty universe**  
  - If no companies meet the cutoff, later steps like allocation break.  
- **Float rounding issues**  
  - Summing weights might not exactly equal 1.0.  
- **Hardcoded assumptions**  
  - Cutoff assumed to be in range `(0 < cutoff < 1)`.  
- **Schema assumptions**  
  - If input CSV is missing columns (`market_cap_m`, `price`), code crashes.  
- **Large datasets**  
  - Very big CSVs may not fit in memory without chunking.  



### 3. Requirements to Identify Errors

- **Input validation**  
  - Assert columns exist (`date`, `company`, `market_cap_m`, `price`).  
  - Check for missing or NaN values.  
- **Sanity checks**  
  - Ensure all prices > 0.  
  - Ensure all market caps > 0.  
  - Ensure cutoff between 0 and 1.  
- **Logging**  
  - Capture companies excluded due to invalid data.  
- **Unit tests**  
  - Small sample data to validate index construction works under edge cases.  



### 4. Gaps vs. Real Market-Weighted Index Funds

- **Dividends**  
  - Dataset ignores dividend payments that affect total returns.  
- **Corporate actions**  
  - Stock splits not accounted for.  
- **Rebalancing frequency**  
  - Real indexes may rebalance quarterly or semi-annually, not daily.    
- **Transaction costs**  
  - Buys and sells assumed frictionless; in reality, commissions & bid/ask spread matter.  
- **Cash holdings**  
  - Index funds may hold a small cash buffer; model assumes 100% invested.   



### When Can These Happen?

- Historical CSV downloaded with missing columns or bad formatting.  
- Vendor updates schema (e.g., renames `market_cap` → `mkt_cap`).  
- Incorrect preprocessing by analyst e.g., duplicate merges
- Extreme market events: stock crashes to 0 price, or market cap anomalies.  
- Simplified dataset from Kaggle or research repo missing float adjustments, dividends, or rebalancing schedule.  

