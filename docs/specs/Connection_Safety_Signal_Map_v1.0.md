# Connection Safety Signal Map v1.0
URIAH_TRADING

This document maps concrete runtime signals (NT8/Rithmic + Python link) into
the Connection Safety Policy v1.0 outcomes.

Policy reference:
- docs/specs/Connection_Safety_Policy_v1.0.md

---

## Safety Inputs

### A) Market/Execution Connectivity (NT8 ↔ Rithmic)
Signals derived from NinjaTrader connection events / connection state.

**Observed pattern:**
`<ConnectionName>: Primary connection=<STATE> Price feed=<STATE>`

---

### B) Controller / Telemetry Integrity (NT8 ↔ Python) — Option A
Signals derived from local file health checks.

#### B1 — Controller heartbeat file
File:
- `data/live/health/controller_heartbeat.json`

Rule:
- **PY_LINK_SAFE = true** if the file exists AND its last write time is within threshold.
- **PY_LINK_NOT_SAFE = true** otherwise.

Threshold (v1.0):
- `HEARTBEAT_MAX_AGE_SEC = 30`

Notes:
- File content can be minimal; freshness is what matters.
- This is an exception-only control: if stale/missing → NOT SAFE.

#### B2 — Local log writeability (append test)
Target:
- `data/live/health/connection_events_YYYY-MM-DD.csv`

Rule:
- **PY_LINK_NOT_SAFE = true** if append fails (permission/disk/path).
- Success does not override a stale heartbeat; it only proves the disk path is writable.

---

## Safety State Derivation

### SAFE condition (must all be true)
- Primary = Connected
- Price feed = Connected
- No hard-error messages (see Message Triggers section)
- PY_LINK_SAFE = true

### NOT SAFE condition
If ANY of the following is true:
- Primary != Connected
- Price feed != Connected
- Any hard-error message is detected
- PY_LINK_NOT_SAFE = true

NOT SAFE must trigger:
- Force Flat if in position
- Lockout until manual reset

---

## Connection State Mapping (deterministic)

Anything other than Connected/Connected is treated as NOT SAFE.

| Primary state | Price feed state | Safety state | Action if FLAT | Action if IN POSITION | Lockout |
|---|---|---|---|---|---|
| Connected | Connected | SAFE | Allow (subject to other gates) | No action | Off |
| Connecting | any | NOT SAFE | Block entry | FORCE FLAT | On |
| Disconnecting | any | NOT SAFE | Block entry | FORCE FLAT | On |
| Disconnected | any | NOT SAFE | Block entry | FORCE FLAT | On |
| any | Connecting | NOT SAFE | Block entry | FORCE FLAT | On |
| any | Disconnecting | NOT SAFE | Block entry | FORCE FLAT | On |
| any | Disconnected | NOT SAFE | Block entry | FORCE FLAT | On |

---

## Message Triggers (hard failures)

These messages force NOT SAFE regardless of state strings.

| Category | Message contains | Safety state | Force Flat | Lockout | Notes |
|---|---|---|---:|---:|---|
| Connection | `Disconnect enforced by broker or 2nd login` | NOT SAFE | Yes | Yes | Compromised session/control risk |
| Connection | `not authorized` | NOT SAFE | Yes | Yes | Hard authorization failure |

Ignored (not safety-related):
- `There are no email share services defined...`

---

## Event Spam / Dedupe Requirements

NT8 may emit repeated messages. Enforcement must be edge-triggered:
- Log every incoming event
- Trigger FORCE FLAT only on transition SAFE → NOT SAFE (state change)

---

## Implementation Checklist (for later coding)

1) Ensure `data/live/health/` exists
2) Python controller writes heartbeat every 5 seconds:
   - update `controller_heartbeat.json` (fresh timestamp)
3) NT8 policy watcher:
   - reads connection state
   - checks heartbeat freshness (`<= 30s`)
   - checks it can append to health CSV
   - computes SAFE/NOT SAFE
4) On NOT SAFE:
   - cancel working orders
   - flatten position immediately
   - emit connection_events row (with not_safe=1, force_flat_triggered=1)
   - lockout = 1 (manual reset required)

---

## Version
- Version: 1.0
- Status: Active