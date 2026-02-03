from glob import glob
import pandas as pd
from pathlib import Path

# Resolve repo root automatically
REPO = Path(__file__).resolve().parents[2]
TRADE_EVENTS_ROOT = REPO / "data" / "live" / "trade_events"


def load_latest_trade_events():
    files = sorted(
        glob(str(TRADE_EVENTS_ROOT / "**" / "trade_events_*.csv"), recursive=True)
    )

    if not files:
        return None, None

    latest = files[-1]
    df = pd.read_csv(latest, parse_dates=["ts_utc"])
    return latest, df


def main():
    path, df = load_latest_trade_events()

    if df is None:
        print(f"\nNo trade_events files found yet under: {TRADE_EVENTS_ROOT}")
        print("That’s normal if the trading system hasn’t written logs yet.")
        return

    print("\n=== URIAH PY QUICK CHECK ===")
    print(f"Loaded file : {path}")
    print(f"Rows        : {len(df):,}")

    print("\nEvent counts:")
    print(df["event_type"].value_counts())

    exits = df[df["event_type"] == "EXIT"].sort_values("ts_utc").tail(10)
    if len(exits):
        cols = [
            "ts_utc",
            "trade_id",
            "system",
            "direction",
            "R_net",
            "net_per_min",
            "fees_trade_total",
            "exit_reason_code",
        ]
        cols = [c for c in cols if c in exits.columns]
        print("\nLast EXIT rows:")
        print(exits[cols].to_string(index=False))
    else:
        print("\nNo EXIT rows yet.")


if __name__ == "__main__":
    main()