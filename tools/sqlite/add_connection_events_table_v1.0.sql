BEGIN;

CREATE TABLE IF NOT EXISTS connection_events (
  event_uid TEXT PRIMARY KEY,
  ts_utc TEXT NOT NULL,

  provider TEXT NOT NULL,
  nt_connection_name TEXT NOT NULL,

  primary_state TEXT NULL,
  pricefeed_state TEXT NULL,

  raw_message TEXT NULL,

  not_safe INTEGER NOT NULL,
  force_flat_triggered INTEGER NOT NULL,
  lockout_active INTEGER NOT NULL,

  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_connection_events_ts
ON connection_events(ts_utc);

COMMIT;