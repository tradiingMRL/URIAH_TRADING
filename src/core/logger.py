# src/core/logger.py
"""
URIAH_TRADING — NDJSON Logger (Contract-Enforced)

- Append-only NDJSON writer
- Enforces required global fields
- Auto-injects ts_utc if missing
- Minimal, no external dependencies
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


SEVERITY_ENUM = {"DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"}


def utc_now_z() -> str:
    """
    Returns ISO-8601 UTC timestamp with Z suffix (matches contract examples).
    Example: 2026-01-31T03:14:15.926Z
    """
    dt = datetime.now(timezone.utc)
    # millisecond precision keeps logs readable and stable
    s = dt.isoformat(timespec="milliseconds")
    return s.replace("+00:00", "Z")


def _ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class LoggerConfig:
    file_path: Path


class NDJSONLogger:
    """
    Contract-enforced NDJSON logger.
    Writes a single JSON object per line (append-only).
    """

    REQUIRED_GLOBAL_FIELDS = {
        "ts_utc",
        "event_type",
        "severity",
        "module",
        "message",
        "correlation_id",
    }

    def __init__(self, file_path: Path):
        self.config = LoggerConfig(file_path=file_path)
        _ensure_parent_dir(self.config.file_path)

    def emit(self, record: Dict[str, Any]) -> None:
        """
        Emit a single NDJSON record after enforcing contract rules.
        """

        # Auto-inject timestamp if missing
        if "ts_utc" not in record or record["ts_utc"] in (None, ""):
            record["ts_utc"] = utc_now_z()

        # Validate required fields
        missing = self.REQUIRED_GLOBAL_FIELDS - set(record.keys())
        if missing:
            raise ValueError(f"Missing required log fields: {sorted(missing)}")

        # Validate severity
        sev = record.get("severity")
        if sev not in SEVERITY_ENUM:
            raise ValueError(f"Invalid severity '{sev}'. Allowed: {sorted(SEVERITY_ENUM)}")

        # Validate event_type not empty
        if not isinstance(record.get("event_type"), str) or not record["event_type"].strip():
            raise ValueError("event_type must be a non-empty string")

        # Write append-only
        with self.config.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log(
        self,
        *,
        event_type: str,
        severity: str,
        module: str,
        message: str,
        correlation_id: str,
        extra: Optional[Dict[str, Any]] = None,
        ts_utc: Optional[str] = None,
    ) -> None:
        """
        Main logging call.

        extra: optional additional key-values to add to the record (e.g. reason_code, trade_id, metrics).
        ts_utc: optional explicit timestamp; otherwise injected.
        """
        record: Dict[str, Any] = {
            "event_type": event_type,
            "severity": severity,
            "module": module,
            "message": message,
            "correlation_id": correlation_id,
        }
        if ts_utc:
            record["ts_utc"] = ts_utc
        if extra:
            record.update(extra)

        self.emit(record)












