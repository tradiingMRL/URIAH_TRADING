# URIAH_TRADING — SQLite Schema v1.0

**Status:** ACTIVE  
**Purpose:** Queryable store for live + backtest logs (System A & B)  
**Source of truth:** Data_Logging_Schema_v1.1.md  
**Design:** Hybrid (typed columns + payload_json for full fidelity)

---

## 1. Database Files (not committed to git)

- Live:
  - `data/live/db/uriah_live.sqlite`
- Backtest:
  - `data/backtest/db/uriah_backtest.sqlite`

**Gitignore must include:**
- `data/`
- `*.sqlite`, `*.db`

---

## 2. Tables

### 2.1 trade_events (core table)
One row per event. Stores:
- key identifiers and time fields
- outcome/reason fields
- PnL / R / fees / time-in-trade (when applicable)
- governance (lockout) fields (when applicable)
- payload_json: full raw event (for long-tail fields)

Primary usage:
- filter by event_type, system, reason codes
- pull all events for one trade_id
- time-of-day studies
- early-exit studies
- gate effectiveness studies (DENY vs PROCEED)

### 2.2 session_summary
One row per session/day.
Primary usage:
- equity curve aggregation
- daily PnL, fees, drawdown, trade counts

### 2.3 ingest_files
Tracks what CSV files have been imported so ingestion is idempotent.

---

## 3. Indexing Strategy

- `trade_events(trade_id, ts_utc)`
- `trade_events(ts_utc)`
- `trade_events(event_type, ts_utc)`
- `trade_events(system, event_type, ts_utc)`
- `trade_events(entry_reason_code)`
- `trade_events(exit_reason_code)`
- `trade_events(tod_bucket)`
- `trade_events(regime_state)`

---

## 4. Ingestion Contract

- CSV writer produces:
  - `data/live/trade_events/YYYY/MM/trade_events_YYYY-MM-DD.csv`
  - `data/live/session/YYYY/MM/session_summary_YYYY-MM-DD.csv`

- Ingest process:
  1) read CSV
  2) map known columns → typed columns
  3) store full row as JSON in `payload_json`
  4) upsert using `event_uid` (hash) to prevent duplicates

---

## 5. Query Examples

### Pull one trade
```sql
SELECT ts_utc, event_type, entry_decision, entry_reason_code, exit_type, exit_reason_code, r_net, pnl_net
FROM trade_events
WHERE trade_id = '20260202-0007'
ORDER BY ts_utc;