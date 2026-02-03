import csv
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from glob import glob
from typing import Any, Dict, List, Optional, Tuple

import sqlite3

# -----------------------------
# Config (project-relative paths)
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DB_PATH = os.path.join(PROJECT_ROOT, "data", "live", "db", "uriah_live.sqlite")

TRADE_EVENTS_GLOB = os.path.join(
    PROJECT_ROOT, "data", "live", "trade_events", "**", "trade_events_*.csv"
)
SESSION_SUMMARY_GLOB = os.path.join(
    PROJECT_ROOT, "data", "live", "session", "**", "session_summary_*.csv"
)

# NEW (A3): connection health events
CONNECTION_EVENTS_GLOB = os.path.join(
    PROJECT_ROOT, "data", "live", "health", "**", "connection_events_*.csv"
)

BATCH_SIZE = 2000


# -----------------------------
# Utilities
# -----------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def now_utc_iso() -> str:
    # Python 3.14+ prefers timezone-aware UTC timestamps
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relpath_under_project(path: str) -> str:
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except Exception:
        return path


def ensure_db_exists(db_path: str) -> None:
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"DB not found at: {db_path}\n"
            f"Create it first and apply schema_v1.0.sql."
        )


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def file_already_ingested(conn: sqlite3.Connection, file_path: str, file_sha: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM ingest_files WHERE file_path = ? AND file_sha256 = ? LIMIT 1;",
        (file_path, file_sha),
    )
    return cur.fetchone() is not None


def mark_file_ingested(conn: sqlite3.Connection, file_path: str, file_sha: str, rows: int) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO ingest_files(file_path, file_sha256, ingested_utc, rows_inserted)
        VALUES (?, ?, datetime('now'), ?);
        """,
        (file_path, file_sha, rows),
    )


def safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    try:
        return float(s)
    except Exception:
        return None


def safe_int01(x: Any) -> Optional[int]:
    if x is None:
        return None
    s = str(x).strip().lower()
    if s in ("", "nan", "none", "null"):
        return None
    if s in ("1", "true", "yes", "y"):
        return 1
    if s in ("0", "false", "no", "n"):
        return 0
    try:
        return 1 if int(float(s)) != 0 else 0
    except Exception:
        return None


def get_first_present(row: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in row and str(row[k]).strip() != "":
            return row[k]
    return None


def stable_event_uid(file_sha: str, row_num_1based: int, row: Dict[str, Any], key_fields: List[str]) -> str:
    """
    Creates a stable per-row UID:
    - depends on file sha + row number + a few key fields
    - resilient to extra columns being added later
    """
    parts = [file_sha, str(row_num_1based)]
    for k in key_fields:
        v = row.get(k, "")
        parts.append("" if v is None else str(v))
    raw = "|".join(parts).encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


# -----------------------------
# trade_events mapping (typed + payload_json)
# -----------------------------
TRADE_EVENTS_TYPED_COLS = [
    "event_uid",
    "ts_utc",
    "trade_id",
    "symbol",
    "system",
    "event_type",
    "direction",
    "session_id",
    "build_id",
    "spec_core_version",
    "spec_l2_version",
    "spec_lr_version",
    "spec_logging_version",
    "ts_exchange",
    "tod_minute",
    "tod_bucket",
    "dow",
    "session_type",
    "account_equity",
    "account_balance",
    "account_unrealized_pnl",
    "lockout_active",
    "lockout_reason",
    "regime_state",
    "risk_gate_pass",
    "risk_gate_reason",
    "regime_gate_pass",
    "regime_gate_reason",
    "entry_decision",
    "entry_reason_code",
    "entry_fill_price",
    "entry_sl_price",
    "entry_tp_price",
    "size_qty",
    "risk_dollars",
    "margin_initial",
    "margin_currency",
    "eval_trigger",
    "eval_elapsed_sec",
    "mgmt_action",
    "mgmt_reason_code",
    "exit_type",
    "exit_reason_code",
    "exit_fill_price",
    "pnl_gross",
    "fees_trade_total",
    "pnl_net",
    "r_gross",
    "r_net",
    "time_in_trade_sec",
    "net_per_min",
    "a_box_reentry_dwell_sec",
    "a_box_reentry_max_depth_ticks",
]


def map_trade_event_row(raw: Dict[str, Any], file_sha: str, row_num_1based: int) -> Tuple[List[Any], str]:
    event_uid = get_first_present(raw, ["event_uid", "event_id", "uid"])
    if event_uid is None:
        key_fields = [
            "ts_utc",
            "trade_id",
            "symbol",
            "system",
            "event_type",
            "direction",
            "entry_reason_code",
            "exit_reason_code",
            "mgmt_reason_code",
        ]
        event_uid = stable_event_uid(file_sha, row_num_1based, raw, key_fields)

    typed: Dict[str, Any] = {k: None for k in TRADE_EVENTS_TYPED_COLS}
    typed["event_uid"] = str(event_uid)

    # key identifiers
    for k, aliases in [
        ("ts_utc", ["ts_utc", "timestamp_utc", "utc_ts"]),
        ("trade_id", ["trade_id", "tradeId", "id"]),
        ("symbol", ["symbol", "instrument"]),
        ("system", ["system", "sys"]),
        ("event_type", ["event_type", "event", "type"]),
    ]:
        v = get_first_present(raw, aliases)
        if v is not None:
            typed[k] = str(v)

    # direct strings
    for k in [
        "direction",
        "session_id",
        "build_id",
        "spec_core_version",
        "spec_l2_version",
        "spec_lr_version",
        "spec_logging_version",
        "ts_exchange",
        "tod_bucket",
        "session_type",
        "lockout_reason",
        "regime_state",
        "risk_gate_reason",
        "regime_gate_reason",
        "entry_decision",
        "entry_reason_code",
        "margin_currency",
        "eval_trigger",
        "mgmt_action",
        "mgmt_reason_code",
        "exit_type",
        "exit_reason_code",
    ]:
        if k in raw and str(raw[k]).strip() != "":
            typed[k] = str(raw[k])

    # floats
    for k in [
        "account_equity",
        "account_balance",
        "account_unrealized_pnl",
        "entry_fill_price",
        "entry_sl_price",
        "entry_tp_price",
        "size_qty",
        "risk_dollars",
        "margin_initial",
        "eval_elapsed_sec",
        "exit_fill_price",
        "pnl_gross",
        "fees_trade_total",
        "pnl_net",
        "r_gross",
        "r_net",
        "time_in_trade_sec",
        "net_per_min",
        "a_box_reentry_dwell_sec",
        "a_box_reentry_max_depth_ticks",
    ]:
        if k in raw:
            typed[k] = safe_float(raw[k])

    # ints
    if "tod_minute" in raw:
        try:
            typed["tod_minute"] = int(float(str(raw["tod_minute"]).strip()))
        except Exception:
            typed["tod_minute"] = None
    if "dow" in raw:
        try:
            typed["dow"] = int(float(str(raw["dow"]).strip()))
        except Exception:
            typed["dow"] = None

    # bool-ish
    for k in ["lockout_active", "risk_gate_pass", "regime_gate_pass"]:
        if k in raw:
            typed[k] = safe_int01(raw[k])

    payload = {
        "raw": raw,
        "_ingest": {
            "file_sha256": file_sha,
            "row_num_1based": row_num_1based,
            "ingested_utc": now_utc_iso(),
        },
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    values = [typed[k] for k in TRADE_EVENTS_TYPED_COLS]
    return values, payload_json


def _insert_trade_event_batch(conn: sqlite3.Connection, batch: List[Tuple[Any, ...]]) -> int:
    placeholders = ",".join(["?"] * (len(TRADE_EVENTS_TYPED_COLS) + 1))
    cols = ",".join(TRADE_EVENTS_TYPED_COLS + ["payload_json"])
    sql = f"INSERT OR IGNORE INTO trade_events ({cols}) VALUES ({placeholders});"
    conn.executemany(sql, batch)
    return len(batch)


def ingest_trade_events_csv(conn: sqlite3.Connection, csv_path: str, file_sha: str) -> int:
    rel = relpath_under_project(csv_path)
    inserted = 0

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch: List[Tuple[Any, ...]] = []
        row_num = 0

        for raw in reader:
            row_num += 1
            values, payload_json = map_trade_event_row(raw, file_sha, row_num)
            batch.append(tuple(values + [payload_json]))

            if len(batch) >= BATCH_SIZE:
                inserted += _insert_trade_event_batch(conn, batch)
                batch.clear()

        if batch:
            inserted += _insert_trade_event_batch(conn, batch)

    mark_file_ingested(conn, rel, file_sha, inserted)
    return inserted


# -----------------------------
# session_summary mapping
# -----------------------------
SESSION_TYPED_COLS = [
    "session_id",
    "ts_start_utc",
    "ts_end_utc",
    "symbol",
    "build_id",
    "spec_logging_version",
    "trades_taken",
    "trades_denied",
    "pnl_net",
    "fees_total",
    "max_drawdown",
    "account_equity_start",
    "account_equity_end",
]


def map_session_row(raw: Dict[str, Any], file_sha: str, row_num_1based: int) -> Tuple[List[Any], str]:
    typed: Dict[str, Any] = {k: None for k in SESSION_TYPED_COLS}

    for k, aliases in [
        ("session_id", ["session_id", "sessionId", "id"]),
        ("ts_start_utc", ["ts_start_utc", "start_utc", "session_start_utc"]),
        ("ts_end_utc", ["ts_end_utc", "end_utc", "session_end_utc"]),
        ("symbol", ["symbol", "instrument"]),
        ("build_id", ["build_id", "build"]),
        ("spec_logging_version", ["spec_logging_version"]),
    ]:
        v = get_first_present(raw, aliases)
        if v is not None:
            typed[k] = str(v)

    for k in ["trades_taken", "trades_denied"]:
        if k in raw:
            try:
                typed[k] = int(float(str(raw[k]).strip()))
            except Exception:
                typed[k] = None

    for k in ["pnl_net", "fees_total", "max_drawdown", "account_equity_start", "account_equity_end"]:
        if k in raw:
            typed[k] = safe_float(raw[k])

    payload = {
        "raw": raw,
        "_ingest": {
            "file_sha256": file_sha,
            "row_num_1based": row_num_1based,
            "ingested_utc": now_utc_iso(),
        },
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    values = [typed[k] for k in SESSION_TYPED_COLS]
    return values, payload_json


def _insert_session_batch(conn: sqlite3.Connection, batch: List[Tuple[Any, ...]]) -> int:
    placeholders = ",".join(["?"] * (len(SESSION_TYPED_COLS) + 1))
    cols = ",".join(SESSION_TYPED_COLS + ["payload_json"])
    sql = f"INSERT OR REPLACE INTO session_summary ({cols}) VALUES ({placeholders});"
    conn.executemany(sql, batch)
    return len(batch)


def ingest_session_summary_csv(conn: sqlite3.Connection, csv_path: str, file_sha: str) -> int:
    rel = relpath_under_project(csv_path)
    inserted = 0

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch: List[Tuple[Any, ...]] = []
        row_num = 0

        for raw in reader:
            row_num += 1
            values, payload_json = map_session_row(raw, file_sha, row_num)
            batch.append(tuple(values + [payload_json]))

            if len(batch) >= BATCH_SIZE:
                inserted += _insert_session_batch(conn, batch)
                batch.clear()

        if batch:
            inserted += _insert_session_batch(conn, batch)

    mark_file_ingested(conn, rel, file_sha, inserted)
    return inserted


# -----------------------------
# connection_events mapping (A3)
# -----------------------------
CONNECTION_EVENTS_TYPED_COLS = [
    "event_uid",
    "ts_utc",
    "provider",
    "nt_connection_name",
    "primary_state",
    "pricefeed_state",
    "raw_message",
    "not_safe",
    "force_flat_triggered",
    "lockout_active",
]


def map_connection_event_row(raw: Dict[str, Any], file_sha: str, row_num_1based: int) -> Tuple[List[Any], str]:
    event_uid = get_first_present(raw, ["event_uid", "event_id", "uid"])
    if event_uid is None:
        key_fields = [
            "ts_utc",
            "provider",
            "nt_connection_name",
            "primary_state",
            "pricefeed_state",
            "raw_message",
            "not_safe",
            "force_flat_triggered",
            "lockout_active",
        ]
        event_uid = stable_event_uid(file_sha, row_num_1based, raw, key_fields)

    typed: Dict[str, Any] = {k: None for k in CONNECTION_EVENTS_TYPED_COLS}
    typed["event_uid"] = str(event_uid)

    # required-ish strings
    for k in ["ts_utc", "provider", "nt_connection_name"]:
        if k in raw and str(raw[k]).strip() != "":
            typed[k] = str(raw[k])

    # optional strings
    for k in ["primary_state", "pricefeed_state", "raw_message"]:
        if k in raw and str(raw[k]).strip() != "":
            typed[k] = str(raw[k])

    # ints 0/1 (required by schema)
    for k in ["not_safe", "force_flat_triggered", "lockout_active"]:
        if k in raw:
            v = safe_int01(raw[k])
            typed[k] = 0 if v is None else v

    payload = {
        "raw": raw,
        "_ingest": {
            "file_sha256": file_sha,
            "row_num_1based": row_num_1based,
            "ingested_utc": now_utc_iso(),
        },
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    values = [typed[k] for k in CONNECTION_EVENTS_TYPED_COLS]
    return values, payload_json


def _insert_connection_event_batch(conn: sqlite3.Connection, batch: List[Tuple[Any, ...]]) -> int:
    placeholders = ",".join(["?"] * (len(CONNECTION_EVENTS_TYPED_COLS) + 1))
    cols = ",".join(CONNECTION_EVENTS_TYPED_COLS + ["payload_json"])
    sql = f"INSERT OR IGNORE INTO connection_events ({cols}) VALUES ({placeholders});"
    conn.executemany(sql, batch)
    return len(batch)


def ingest_connection_events_csv(conn: sqlite3.Connection, csv_path: str, file_sha: str) -> int:
    rel = relpath_under_project(csv_path)
    inserted = 0

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch: List[Tuple[Any, ...]] = []
        row_num = 0

        for raw in reader:
            row_num += 1
            values, payload_json = map_connection_event_row(raw, file_sha, row_num)
            batch.append(tuple(values + [payload_json]))

            if len(batch) >= BATCH_SIZE:
                inserted += _insert_connection_event_batch(conn, batch)
                batch.clear()

        if batch:
            inserted += _insert_connection_event_batch(conn, batch)

    mark_file_ingested(conn, rel, file_sha, inserted)
    return inserted


# -----------------------------
# Main
# -----------------------------
@dataclass
class IngestResult:
    kind: str
    files_seen: int
    files_ingested: int
    rows_inserted: int


def ingest_kind(conn: sqlite3.Connection, kind: str, pattern: str) -> IngestResult:
    paths = sorted(glob(pattern, recursive=True))
    seen = len(paths)
    ingested_files = 0
    inserted_rows = 0

    for p in paths:
        file_sha = sha256_file(p)
        rel = relpath_under_project(p)

        if file_already_ingested(conn, rel, file_sha):
            continue

        if kind == "trade_events":
            n = ingest_trade_events_csv(conn, p, file_sha)
        elif kind == "session_summary":
            n = ingest_session_summary_csv(conn, p, file_sha)
        elif kind == "connection_events":
            n = ingest_connection_events_csv(conn, p, file_sha)
        else:
            raise ValueError(f"Unknown kind: {kind}")

        ingested_files += 1
        inserted_rows += n

    return IngestResult(kind, seen, ingested_files, inserted_rows)


def main() -> int:
    ensure_db_exists(DB_PATH)

    print(f"DB: {relpath_under_project(DB_PATH)}")
    conn = connect(DB_PATH)

    try:
        conn.execute("BEGIN;")
        r1 = ingest_kind(conn, "trade_events", TRADE_EVENTS_GLOB)
        r2 = ingest_kind(conn, "session_summary", SESSION_SUMMARY_GLOB)
        r3 = ingest_kind(conn, "connection_events", CONNECTION_EVENTS_GLOB)
        conn.commit()

        print(f"trade_events: files_seen={r1.files_seen} files_ingested={r1.files_ingested} rows_inserted={r1.rows_inserted}")
        print(f"session_summary: files_seen={r2.files_seen} files_ingested={r2.files_ingested} rows_inserted={r2.rows_inserted}")
        print(f"connection_events: files_seen={r3.files_seen} files_ingested={r3.files_ingested} rows_inserted={r3.rows_inserted}")
        return 0
    except Exception as e:
        conn.rollback()
        print("INGEST FAILED:", repr(e))
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())