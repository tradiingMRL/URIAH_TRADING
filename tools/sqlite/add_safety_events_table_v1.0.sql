-- add_safety_events_table_v1.0.sql
-- URIAH_TRADING: Safety lifecycle events (force-flat, lockout, reset)

BEGIN;

CREATE TABLE IF NOT EXISTS safety_events (
  event_uid TEXT PRIMARY KEY,             -- UUID
  ts_utc TEXT NOT NULL,                   -- ISO-8601 UTC

  event_type TEXT NOT NULL,               -- SAFETY_NOT_SAFE | FORCE_FLAT_ISSUED | LOCKOUT_ENTERED | RESET_REQUESTED | RESET_ACCEPTED | RESET_REJECTED
  source TEXT NOT NULL,                   -- NT8 | RITHMIC | PY_CONTROLLER

  reason_code TEXT NOT NULL,              -- short code, e.g. HEARTBEAT_STALE, NT8_DISCONNECTED, MANUAL_RESET
  details TEXT NULL,                      -- short human-readable detail

  not_safe INTEGER NOT NULL DEFAULT 0,     -- 0/1
  lockout_active INTEGER NOT NULL DEFAULT 0, -- 0/1

  reset_flag_detected INTEGER NOT NULL DEFAULT 0, -- 0/1 (only for reset events)
  reset_result TEXT NULL,                 -- ACCEPTED | REJECTED (nullable unless reset event)
  reset_fail_reason TEXT NULL,            -- nullable
  safety_snapshot_json TEXT NOT NULL       -- JSON snapshot of safety inputs at time of event
);

CREATE INDEX IF NOT EXISTS idx_safety_events_ts
  ON safety_events(ts_utc);

CREATE INDEX IF NOT EXISTS idx_safety_events_type
  ON safety_events(event_type);

CREATE INDEX IF NOT EXISTS idx_safety_events_lockout
  ON safety_events(lockout_active, ts_utc);

COMMIT;