import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

# DB path (project-relative)
DB_PATH = os.path.join("data", "live", "db", "uriah_live.sqlite")

# Heartbeat file (project-relative)
HEARTBEAT_PATH = os.path.join("data", "live", "health", "controller_heartbeat.json")


def utc_now_iso() -> str:
    # ISO-8601 UTC with Z
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_controller_heartbeat() -> dict:
    """
    Best-effort read. Never raises. Returns a snapshot dict.
    """
    snap = {
        "heartbeat_present": 0,
        "heartbeat_ts_utc": None,
        "heartbeat_age_sec": None,
        "heartbeat_status": None,
        "heartbeat_source": None,
        "heartbeat_read_error": None,
    }
    try:
        if not os.path.exists(HEARTBEAT_PATH):
            return snap

        with open(HEARTBEAT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        snap["heartbeat_present"] = 1
        snap["heartbeat_ts_utc"] = data.get("ts_utc")
        snap["heartbeat_status"] = data.get("status")
        snap["heartbeat_source"] = data.get("source")

        # Attempt age calculation if ts_utc is parseable
        ts = snap["heartbeat_ts_utc"]
        if ts:
            # Accept both "...Z" and timezone-aware ISO strings
            ts_norm = ts.replace("Z", "+00:00")
            hb_dt = datetime.fromisoformat(ts_norm)
            age = (datetime.now(timezone.utc) - hb_dt).total_seconds()
            snap["heartbeat_age_sec"] = round(age, 3)

        return snap

    except Exception as e:
        snap["heartbeat_read_error"] = str(e)
        return snap


def build_safety_snapshot_json(
    nt8_primary_state: str = None,
    nt8_pricefeed_state: str = None,
    rithmic_state: str = None,
    lockout_active: int = None,
) -> str:
    """
    Minimal snapshot for now.
    Later we can extend without changing DB schema.
    """
    hb = read_controller_heartbeat()

    snapshot = {
        "nt8_primary_state": nt8_primary_state,
        "nt8_pricefeed_state": nt8_pricefeed_state,
        "rithmic_state": rithmic_state,
        "lockout_active": lockout_active,
        "controller_heartbeat": hb,
    }
    return json.dumps(snapshot, separators=(",", ":"), ensure_ascii=False)


def log_safety_event(
    event_type: str,
    source: str,
    reason_code: str,
    details: str = None,
    not_safe: int = 0,
    lockout_active: int = 0,
    reset_flag_detected: int = 0,
    reset_result: str = None,
    reset_fail_reason: str = None,
    nt8_primary_state: str = None,
    nt8_pricefeed_state: str = None,
    rithmic_state: str = None,
) -> str:
    """
    Writes one row into SQLite safety_events.
    Returns event_uid.

    IMPORTANT:
    - No business logic in here.
    - If DB write fails, raise immediately (visibility > silence).
    """
    event_uid = str(uuid.uuid4())
    ts_utc = utc_now_iso()

    safety_snapshot_json = build_safety_snapshot_json(
        nt8_primary_state=nt8_primary_state,
        nt8_pricefeed_state=nt8_pricefeed_state,
        rithmic_state=rithmic_state,
        lockout_active=lockout_active,
    )

    row = (
        event_uid,
        ts_utc,
        event_type,
        source,
        reason_code,
        details,
        int(not_safe),
        int(lockout_active),
        int(reset_flag_detected),
        reset_result,
        reset_fail_reason,
        safety_snapshot_json,
    )

    sql = """
    INSERT INTO safety_events (
      event_uid, ts_utc, event_type, source,
      reason_code, details,
      not_safe, lockout_active,
      reset_flag_detected, reset_result, reset_fail_reason,
      safety_snapshot_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    # Ensure folder exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(sql, row)
        conn.commit()

    return event_uid


if __name__ == "__main__":
    # Manual test event (safe to run repeatedly)
    uid = log_safety_event(
        event_type="RESET_REQUESTED",
        source="PY_CONTROLLER",
        reason_code="MANUAL_TEST",
        details="manual smoke test for safety_events logger",
        not_safe=0,
        lockout_active=1,
        reset_flag_detected=1,
        reset_result=None,
        reset_fail_reason=None,
        nt8_primary_state="Unknown",
        nt8_pricefeed_state="Unknown",
        rithmic_state="Unknown",
    )
    print(f"Inserted safety_events row: {uid}")