# io/sources/csv_replay.py

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from contracts.messages import MarketFeatures
from utils.exceptions import ContractError, DataQualityError

REQUIRED_COLUMNS = [
    "timestamp",
    "instrument",
    "price",
    "volume",
    "atr_fast",
    "atr_slow",
    "vol_norm",
    "velocity",
]


def _parse_utc_timestamp(ts: str) -> datetime:
    """
    Parse ISO8601 timestamp.
    If timezone is missing, assume UTC (fail-closed policy can be tightened later).
    """
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError as e:
        raise ContractError(f"Invalid timestamp format: {ts}") from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _require_columns(fieldnames) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in (fieldnames or [])]
    if missing:
        raise ContractError(f"CSV missing required columns: {missing}")


def stream_csv_replay(
    path: str | Path,
    *,
    max_rows: Optional[int] = None,
) -> Iterator[MarketFeatures]:

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _require_columns(reader.fieldnames)

        for i, row in enumerate(reader):
            if max_rows is not None and i >= max_rows:
                break

            try:
                features = MarketFeatures(
                    timestamp=_parse_utc_timestamp(row["timestamp"]),
                    instrument=row["instrument"].strip(),
                    price=float(row["price"]),
                    volume=float(row["volume"]),
                    atr_fast=float(row["atr_fast"]),
                    atr_slow=float(row["atr_slow"]),
                    vol_norm=float(row["vol_norm"]),
                    velocity=float(row["velocity"]),
                )
            except KeyError as e:
                raise ContractError(f"CSV row missing field: {e}") from e
            except ValueError as e:
                raise DataQualityError(f"Invalid numeric value in row: {row}") from e

            if not features.instrument:
                raise ContractError("Instrument is empty")

            if features.price <= 0:
                raise DataQualityError(f"Non-positive price: {features.price}")

            yield features