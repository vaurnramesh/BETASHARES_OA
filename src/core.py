import pandas as pd


def index_construct(df, date, cutoff, capital):
    """
    Parameters
    ----------
    df : pd.DataFrame
        Must include columns ["date", "company", "market_cap_m", "price"]
    date : str or datetime
        Date to filter the data for
    cutoff : float
        Cumulative market-cap percentile threshold (0-1)
    capital : float
        Total capital to allocate

    Returns
    -------
    total_mc : float - Total market capitalization of all stocks on the date
    universe_in : pd.DataFrame - Selected stocks with columns:
    universe_out : pd.DataFrame - Excluded stocks (cumulative > cutoff)
            
    Output Table (universe_in):

    | Company | Market cap | Weight | Cumulative | Allocation | Shares |
    |---------|------------|--------|------------|-----------|--------|
    | A       | 1000       | 0.10   | 0.10       | 10,000,000| 500    |
    | B       | 900        | 0.09   | 0.19       | 9,000,000 | 300    |
    | C       | 800        | 0.08   | 0.27       | 8,000,000 | 200    |

    - Weight = Market Cap / Sum of Market Cap

    - Cumulative is only used for estimating cutoff 

    - Allocation = Capital x Weight = 100_000_000 x df[weight]

    - Shares = Allocation / current stock price 
    """

    # -----------------------
    # Input Validation
    # -----------------------
    required_cols = {"date", "company", "market_cap_m", "price"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Input DataFrame missing columns: {missing_cols}")

    if cutoff <= 0 or cutoff > 1:
        raise ValueError(f"Cutoff must be between 0 and 1. Got: {cutoff}")

    if capital <= 0:
        raise ValueError(f"Capital must be positive. Got: {capital}")
    
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    if date not in df["date"].values:
        raise ValueError(f"Date {date} not found in DataFrame.")
    

   # Filter by date
    subset = df[df["date"] == date].copy()

    # Order companies by descending market cap
    subset = subset.sort_values(by="market_cap_m", ascending=False)

    # Compute the total market cap of all stocks
    total_mc = subset["market_cap_m"].sum()

    # Calculate each company’s market cap weight and cumulative weight
    subset["weight"] = subset["market_cap_m"] / total_mc
    subset["cumulative"] = subset["weight"].cumsum()

    # Select companies up to the 85th cumulative percentile (by market cap weight)
    universe_in = subset.loc[subset["cumulative"] <= cutoff].copy()
    # Companies that do NOT make the cutoff
    universe_out = subset.loc[subset["cumulative"] > cutoff].copy()

    # Allocate $100 million to the selected stocks, and calculate the number of shares to buy for each
    universe_in["allocation"] = capital * universe_in["weight"]
    universe_in["shares"] = universe_in["allocation"] / universe_in["price"]

    return total_mc, universe_in, universe_out


def rebalancing(df, old_date, new_date, index_construct, **kwargs):
    """
    Rebalance a portfolio between two dates based on index construction.

    Output Table (combined):

    | Company | shares_old | allocation_old | shares | allocation | Price | trade_shares | trade_value | action  |
    |---------|------------|----------------|--------|-----------|-------|--------------|------------|--------|
    | A       | 500        | 10,000,000     | 550    | 11,000,000| 20    | 50           | 1,000,000  | ADJUST |
    | B       | 300        | 9,000,000      | 0      | 0         | 30    | -300         | -9,000,000 | SELL   |
    | C       | 0          | 0              | 200    | 8,000,000 | 40    | 200          | 8,000,000  | BUY    |

    Formulaes: 

    - trade_shares = shares - shares_old
    - trade_value = trade_shares * price
    - shares_old & allocation_old = from old date portfolio
    - shares * allocation = from new date portfolio (index_construct)
    - action:
        - "ADJUST" → stock remains in portfolio, weight changed
        - "BUY" → stock added to portfolio 
        - "SELL" → stock removed from portfolio 
        - "IGNORE" → stock not in portfolio on either date (both universe)

    """


    # Index calculation for old date
    total_mc_old, universe_in_old, universe_out_old = index_construct(df, old_date, **kwargs)

    # Index calculation for new date
    total_mc_new, universe_in_new, universe_out_new = index_construct(df, new_date, **kwargs)


    # Identify stock sets
    old_in_set = set(universe_in_old["company"])
    old_out_set = set(universe_out_old["company"])
    new_in_set = set(universe_in_new["company"])
    new_out_set = set(universe_out_new["company"])

    # Determine actions using Inner Join
    hold_set = old_in_set & new_in_set       # Keep stocks
    sell_set = old_in_set & new_out_set      # Sell stocks
    buy_set = old_out_set & new_in_set       # Buy stocks
    ignore_set = old_out_set & new_out_set   # Ignore stocks

    # Prepare combined dataframe
    combined = pd.DataFrame()

    # These stocks will remain in the universe. 
    # ADJUST label is being used -
    # because even if a stock stays in the universe, its weight has changed and may need to buy or sell some shares 
    hold_df = universe_in_new[universe_in_new["company"].isin(hold_set)].copy()
    hold_df["shares_old"] = universe_in_old.set_index("company").loc[hold_df["company"], "shares"].values
    hold_df["allocation_old"] = universe_in_old.set_index("company").loc[hold_df["company"], "allocation"].values
    hold_df["trade_shares"] = hold_df["shares"] - hold_df["shares_old"]
    hold_df["trade_value"] = hold_df["trade_shares"] * hold_df["price"]
    hold_df["action"] = ["ADJUST"] * len(hold_df)
    combined = pd.concat([combined, hold_df], ignore_index=True)


    # SELL
    sell_df = universe_in_old[universe_in_old["company"].isin(sell_set)].copy()
    sell_df["shares_old"] = sell_df["shares"]
    sell_df["allocation_old"] = sell_df["allocation"]
    sell_df["shares"] = 0
    sell_df["allocation"] = 0
    sell_df["trade_shares"] = -sell_df["shares_old"]
    sell_df["trade_value"] = sell_df["trade_shares"] * sell_df["price"]
    sell_df["action"] = ["SELL"] * len(sell_df)
    combined = pd.concat([combined, sell_df], ignore_index=True)

    # BUY
    buy_df = universe_in_new[universe_in_new["company"].isin(buy_set)].copy()
    buy_df["shares_old"] = 0
    buy_df["allocation_old"] = 0
    buy_df["trade_shares"] = buy_df["shares"]
    buy_df["trade_value"] = buy_df["trade_shares"] * buy_df["price"]
    buy_df["action"] = ["BUY"] * len(buy_df)
    combined = pd.concat([combined, buy_df], ignore_index=True)

    # IGNORE (optional, usually not included)
    ignore_df = universe_out_new[universe_out_new["company"].isin(ignore_set)].copy()
    ignore_df["shares_old"] = 0
    ignore_df["allocation_old"] = 0
    ignore_df["shares"] = 0
    ignore_df["allocation"] = 0
    ignore_df["trade_shares"] = 0
    ignore_df["trade_value"] = 0
    ignore_df["action"] = ["IGNORE"] * len(ignore_df)
    combined = pd.concat([combined, ignore_df], ignore_index=True)

    # Reorder columns for clarity
    combined = combined[[
        "company", "shares_old", "allocation_old",
        "shares", "allocation",
        "price", "trade_shares", "trade_value", "action"
    ]]

    return combined


def portfolio_summary(combined, round_digits):
    """
    @output params
    - old_portfolio_value: Total dollar value of the portfolio on the old date
                           (sum of shares_old x price).
    - new_portfolio_value: Total dollar value of the portfolio on the new date
                           (sum of shares x price).
    - total_trade_value: Aggregate absolute dollar value traded 
                         (sum of |trade_value| across all actions)
    - buy_value: Total dollar value of positions initiated (action == "BUY")
    - sell_value: Total dollar value of positions liquidated (action == "SELL")
    - adjust_value: Total incremental dollar value of adjustments 
                    for holdings that remain in the index (action == "ADJUST")
    - dollar_turnover_pct: Portfolio turnover as a percentage of the new portfolio value.
                Calculated as sum of absolute trade values divided by the new portfolio value:

                turnover_pct = total_trade_value / new_portfolio_value

    - shares_turnover_pct: Portfolio turnover measured in shares (industry standard). 
                Calculated as the sum of absolute shares traded across all actions 
                divided by the average number of shares held during the period:
  
                shares_turnover_pct = (SUM(|trade_shares|) / (SUM(shares_old + shares)) / 2) x 100
  
                This gives a percentage indicating how much of the portfolio's holdings 
                were replaced or traded in terms of number of shares, independent of 
                dollar value.
    - total_new_shares: Total number of shares purchased in "BUY" actions
    - total_sold_shares: Total number of shares sold in "SELL" actions
    - new_buys: DataFrame of all companies newly added ("BUY"), including
                company, shares, trade_shares, trade_value
    - sold_stocks: DataFrame of all companies fully sold ("SELL"), including
                   company, shares_old, trade_shares, trade_value
    """
    
    # Filter out ignored stocks
    portfolio_stocks = combined[combined["action"] != "IGNORE"].copy()

    # Old and new portfolio values
    old_value = float((portfolio_stocks["shares_old"] * portfolio_stocks["price"]).sum())
    new_value = float((portfolio_stocks["shares"] * portfolio_stocks["price"]).sum())

    # Trading stats
    total_trade_value = float(portfolio_stocks["trade_value"].abs().sum())
    buys = float(portfolio_stocks[portfolio_stocks["action"] == "BUY"]["trade_value"].sum())
    sells = float(portfolio_stocks[portfolio_stocks["action"] == "SELL"]["trade_value"].sum())
    adjusts = float(portfolio_stocks[portfolio_stocks["action"] == "ADJUST"]["trade_value"].sum())

    dollar_turnover_pct = total_trade_value / new_value if new_value > 0 else 0

    # Share-based turnover (industry standard)
    portfolio_stocks["avg_shares"] = (portfolio_stocks["shares_old"] + portfolio_stocks["shares"]) / 2
    total_avg_shares = portfolio_stocks["avg_shares"].sum()
    share_turnover_pct = portfolio_stocks["trade_shares"].abs().sum() / total_avg_shares * 100


    # New equities purchased
    new_buys = portfolio_stocks[portfolio_stocks["action"] == "BUY"].copy()
    total_new_shares = new_buys["trade_shares"].sum()
    new_buys_list = new_buys[["company", "shares", "trade_shares", "trade_value"]]

    # Equities sold
    sold_stocks = portfolio_stocks[portfolio_stocks["action"] == "SELL"].copy()
    total_sold_shares = sold_stocks["shares_old"].sum()
    sold_list = sold_stocks[["company", "shares_old", "trade_shares", "trade_value"]]

    # Prepare summary dictionary
    summary = {
        "old_portfolio_value": round(old_value, round_digits),
        "new_portfolio_value": round(new_value, round_digits),
        "total_trade_value": round(total_trade_value, round_digits),
        "buy_value": round(buys, round_digits),
        "sell_value": round(sells, round_digits),
        "adjust_value": round(adjusts, round_digits),
        "dollar_turnover_pct": f"{dollar_turnover_pct:.2%}",
        "share_turnover_pct": f"{share_turnover_pct:.2f}%",
        "total_new_shares": int(total_new_shares),
        "total_sold_shares": int(total_sold_shares),
        "new_buys": new_buys_list.reset_index(drop=True),
        "sold_stocks": sold_list.reset_index(drop=True)
    }

    return summary






