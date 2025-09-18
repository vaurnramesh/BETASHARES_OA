# Technical Assessment for Software Engineer Position - Variant 3 - Index Rebalance

## 📘 Scenario
You are a software engineer at Betashares. Your task is to demonstrate your ability to work with financial data, apply quantitative logic, and write clear, maintainable code. Using Python, or another language of your choice, you will create a script that constructs and rebalances a market cap weighted index fund.

Market cap weighted indices are based upon cumulative market cap within an index. An index fund will specify what proportion of a universe can be included within it.
The fund will then buy the stocks in the index based upon their market cap weight. The fund will also rebalance periodically, which may result in buying and selling stocks.

## 📋 Task
You are provided with a CSV file containing the following columns:
- Date
- Company
- Market Cap
- Price

Your tasks are as follows:

### 1. Index Construction (First Date: 2025-04-08)
1. Filter the data for the date `2025-04-08`.
2. Order companies by descending market cap.
3. Compute the total market cap of all stocks.
4. Calculate each company’s market cap weight and cumulative weight.
5. Refer to this example – this is the first few rows of the output:

| Company | Market cap | Weight | Cumulative |
|---------|------------|--------|------------|
| A       | 1000       | 0.10   | 0.10       |
| B       | 900        | 0.09   | 0.19       |
| C       | 800        | 0.08   | 0.27       |
| ...     | ...        | ...    | ...        |

6. Select companies up to the 85th cumulative percentile (by market cap weight).
7. Allocate $100 million to the selected stocks, and calculate the number of shares to buy for each (using the price).

### 2. Rebalancing (Second Date: 2025-05-08)
1. Filter the data for the second date (`2025-05-08`).
2. Repeat steps 2–5 from the Index Construction section on this new data set.
3. Determine a new fund universe, i.e., which stocks make the cutoff (85th percentile) on the new market caps.
   - If a stock was not in the original list BUT is in the new universe, it will be bought.
   - If a stock is in the original list BUT not in the new universe, it will be sold from the fund.
4. Calculate:
   - The value of your portfolio at the second date
   - The quantity of any new equities purchased by the fund.
   - Identify which equity(ies) are being sold and their total value.

### 3. Scenarios & Real World Considerations
- In a commented section, list and describe in the script as many scenarios as you can where:
  - The data is incorrect (e.g., formatting, content).
  - The code might break.
- Write the necessary requirements to be able to identify your sources of error.
- Using your knowledge & research of market weighted index funds, list and describe what may be missing from this dataset & hence the code.

## 📋 Requirements
- Use clear naming and folder structure.
- Code should be well-structured and commented.
- Include a `README.md` with setup and run instructions.
- (Optional) Include unit tests.

## 💡 Bonus Points
- Suggestions for future improvements.

## 🕒 Time Limit
Estimated time: 90 minutes

## 📦 Submission
- Submit via GitHub repo or zip file.
- Include all code, data, and documentation.