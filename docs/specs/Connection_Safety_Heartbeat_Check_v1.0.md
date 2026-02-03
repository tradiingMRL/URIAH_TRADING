# Connection Safety — Heartbeat Check v1.0
URIAH_TRADING

This document defines the deterministic heartbeat freshness check used by
execution (NT8) to assess controller / Python link safety.

Policy reference:
- Connection_Safety_Policy_v1.0.md
- Connection_Safety_Signal_Map_v1.0.md

---

## Heartbeat Source

File:
- data/live/health/controller_heartbeat.json

Expected fields:
- ts_utc (ISO-8601 UTC)
- status
- source

Content is informational; **freshness is authoritative**.

---

## Freshness Rule (v1.0)

Let:
- T_now = current UTC time at execution
- T_hb = ts_utc parsed from heartbeat file

Define:
- HEARTBEAT_MAX_AGE_SEC = 30

### PY_LINK_SAFE
If:
- Heartbeat file exists AND
- (T_now − T_hb) ≤ HEARTBEAT_MAX_AGE_SEC

### PY_LINK_NOT_SAFE
If ANY are true:
- Heartbeat file missing
- Heartbeat file unreadable
- ts_utc parse failure
- (T_now − T_hb) > HEARTBEAT_MAX_AGE_SEC

---

## Safety Outcome

If PY_LINK_NOT_SAFE:
- Treat as NOT SAFE
- Apply Connection Safety Policy:
  - Force Flat immediately if in position
  - Enter LOCKOUT
  - Block all new orders until manual reset

---

## Evaluation Frequency

- Execution layer must evaluate heartbeat freshness:
  - On every connection-state event
  - At a fixed interval (≤ 5 seconds) while connected

---

## Logging Requirements

On transition SAFE → NOT SAFE due to heartbeat:
- Emit connection_events with:
  - provider = CONTROLLER
  - not_safe = 1
  - raw_message = HEARTBEAT_STALE
- Emit FORCE_FLAT trade_events (if applicable)
- Record LOCKOUT activation

---

## Version
- Version: 1.0
- Status: Active