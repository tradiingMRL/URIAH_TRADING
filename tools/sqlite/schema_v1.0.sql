-- URIAH_TRADING SQLite Schema v1.0
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('schema_version', '1.0');
INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('created_utc', datetime('now'));

CREATE TABLE IF NOT EXISTS trade_events (
  event_uid TEXT PRIMARY KEY,

  ts_utc TEXT NOT NULL,
  trade_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  system TEXT NOT NULL CHECK (system IN ('A','B')),
  event_type TEXT NOT NULL,
  direction TEXT NULL,
  session_id TEXT NULL,
  build_id TEXT NULL,

  spec_core_version TEXT NULL,
  spec_l2_version TEXT NULL,
  spec_lr_version TEXT NULL,
  spec_logging_version TEXT NULL,

  ts_exchange TEXT NULL,
  tod_minute INTEGER NULL,
  tod_bucket TEXT NULL,
  dow INTEGER NULL,
  session_type TEXT NULL,

  account_equity REAL NULL,
  account_balance REAL NULL,
  account_unrealized_pnl REAL NULL,

  lockout_active INTEGER NULL CHECK (lockout_active IN (0,1)),
  lockout_reason TEXT NULL,

  regime_state TEXT NULL,
  risk_gate_pass INTEGER NULL CHECK (risk_gate_pass IN (0,1)),
  risk_gate_reason TEXT NULL,
  regime_gate_pass INTEGER NULL CHECK (regime_gate_pass IN (0,1)),
  regime_gate_reason TEXT NULL,

  entry_decision TEXT NULL,
  entry_reason_code TEXT NULL,

  entry_fill_price REAL NULL,
  entry_sl_price REAL NULL,
  entry_tp_price REAL NULL,
  size_qty REAL NULL,
  risk_dollars REAL NULL,
  margin_initial REAL NULL,
  margin_currency TEXT NULL,

  eval_trigger TEXT NULL,
  eval_elapsed_sec REAL NULL,
  mgmt_action TEXT NULL,
  mgmt_reason_code TEXT NULL,

  exit_type TEXT NULL,
  exit_reason_code TEXT NULL,
  exit_fill_price REAL NULL,
  pnl_gross REAL NULL,
  fees_trade_total REAL NULL,
  pnl_net REAL NULL,
  r_gross REAL NULL,
  r_net REAL NULL,
  time_in_trade_sec REAL NULL,
  net_per_min REAL NULL,

  a_box_reentry_dwell_sec REAL NULL,
  a_box_reentry_max_depth_ticks REAL NULL,

  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_summary (
  session_id TEXT PRIMARY KEY,
  ts_start_utc TEXT NOT NULL,
  ts_end_utc TEXT NOT NULL,

  symbol TEXT NULL,
  build_id TEXT NULL,
  spec_logging_version TEXT NULL,

  trades_taken INTEGER NULL,
  trades_denied INTEGER NULL,

  pnl_net REAL NULL,
  fees_total REAL NULL,
  max_drawdown REAL NULL,

  account_equity_start REAL NULL,
  account_equity_end REAL NULL,

  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_files (
  file_path TEXT PRIMARY KEY,
  file_sha256 TEXT NOT NULL,
  ingested_utc TEXT NOT NULL DEFAULT (datetime('now')),
  rows_inserted INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_trade_events_trade_ts
  ON trade_events(trade_id, ts_utc);

CREATE INDEX IF NOT EXISTS ix_trade_events_ts
  ON trade_events(ts_utc);

CREATE INDEX IF NOT EXISTS ix_trade_events_type_ts
  ON trade_events(event_type, ts_utc);

CREATE INDEX IF NOT EXISTS ix_trade_events_system_type_ts
  ON trade_events(system, event_type, ts_utc);

CREATE INDEX IF NOT EXISTS ix_trade_events_entry_reason
  ON trade_events(entry_reason_code);

CREATE INDEX IF NOT EXISTS ix_trade_events_exit_reason
  ON trade_events(exit_reason_code);

CREATE INDEX IF NOT EXISTS ix_trade_events_tod_bucket
  ON trade_events(tod_bucket);

CREATE INDEX IF NOT EXISTS ix_trade_events_regime
  ON trade_events(regime_state);

COMMIT;