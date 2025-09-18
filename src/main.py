from core import index_construct, rebalancing, portfolio_summary
from utils import load_data, save_dataframe, save_summary_json
from pathlib import Path

csv_name = "./data/input/market_capitalisation.csv"
csv_output = "./data/output/output.csv"
json_output = "./data/output/summary.json"

def main():
    data = load_data(csv_name)
    if data.empty:
        raise ValueError(f"No data loaded from {csv_name}")

    combined = rebalancing(
        df=data,
        old_date="2025-08-04",
        new_date="2025-08-05",
        index_construct=index_construct,
        cutoff=0.85,
        capital=100_000_000
    )
    summary_stats = portfolio_summary(combined, 2)

    Path(csv_output).parent.mkdir(parents=True, exist_ok=True)
    Path(json_output).parent.mkdir(parents=True, exist_ok=True)

    save_dataframe(df=combined, csv_output=csv_output)
    save_summary_json(summary=summary_stats, file_path=json_output)


if __name__ == "__main__":
    main()

    