import pandas as pd
import json
from pathlib import Path



def load_data(csv_name: str) -> pd.DataFrame:
    df = pd.read_csv(csv_name)
    df = df.dropna(subset=["date", "market_cap_m", "price"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["market_cap_m"] = pd.to_numeric(df["market_cap_m"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return df


def save_dataframe(df, csv_output, index=False):
    file_path = Path(csv_output)
    df.to_csv(file_path, index=index)
    print(f"DataFrame saved to {file_path}")


def save_summary_json(summary, file_path):
    
    file_path = Path(file_path)

    # Convert any DataFrames in the summary to list of dicts for JSON serialization
    serializable_summary = {}
    for k, v in summary.items():
        if isinstance(v, pd.DataFrame):
            serializable_summary[k] = v.to_dict(orient="records")
        else:
            serializable_summary[k] = v

    with open(file_path, "w") as f:
        json.dump(serializable_summary, f, indent=4)

    print(f"Summary saved as JSON to {file_path}")