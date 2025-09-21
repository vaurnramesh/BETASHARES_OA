import pandas as pd
from src.core import rebalancing

def mock_index_construct(df, date, **kwargs):
    """
    Minimal stub for index_construct that returns deterministic outputs
    based on the 'date' string.
    """
    if date == "old":
        universe_in = pd.DataFrame([
            {"company": "A", "shares": 500, "allocation": 10_000_000, "price": 20},
            {"company": "B", "shares": 300, "allocation": 9_000_000, "price": 30},
        ])
        universe_out = pd.DataFrame([
            {"company": "C", "shares": 0, "allocation": 0, "price": 40},
        ])
        return (19_000_000, universe_in, universe_out)

    elif date == "new":
        universe_in = pd.DataFrame([
            {"company": "A", "shares": 550, "allocation": 11_000_000, "price": 20},
            {"company": "C", "shares": 200, "allocation": 8_000_000, "price": 40},
        ])
        universe_out = pd.DataFrame([
            {"company": "B", "shares": 0, "allocation": 0, "price": 30},
        ])
        return (19_000_000, universe_in, universe_out)

    else:
        raise ValueError("Unexpected date")


def test_rebalancing():
    # Dummy df
    df = pd.DataFrame()

    result = rebalancing(df, "old", "new", mock_index_construct)

    # Sort for consistency
    result = result.sort_values("company").reset_index(drop=True)

    # Expected structure: A adjusted, B sold, C bought
    assert set(result["company"]) == {"A", "B", "C"}
    assert result.loc[result["company"] == "A", "action"].item() == "ADJUST"
    assert result.loc[result["company"] == "B", "action"].item() == "SELL"
    assert result.loc[result["company"] == "C", "action"].item() == "BUY"

    # Check A adjustments
    row_a = result[result["company"] == "A"].iloc[0]
    assert row_a["shares_old"] == 500
    assert row_a["shares"] == 550
    assert row_a["trade_shares"] == 50
    assert row_a["trade_value"] == 1000  # 50 * 20

    # Check B sell
    row_b = result[result["company"] == "B"].iloc[0]
    assert row_b["shares_old"] == 300
    assert row_b["shares"] == 0
    assert row_b["trade_shares"] == -300
    assert row_b["trade_value"] == -9_000 # Selling all holdings

    # Check C buy
    row_c = result[result["company"] == "C"].iloc[0]
    assert row_c["shares_old"] == 0
    assert row_c["shares"] == 200
    assert row_c["trade_shares"] == 200
    assert row_c["trade_value"] == 8_000 # Buying new holdings
