# URIAH_TRADING — Safety Module v1.0 (LOCKED)

## 1. Purpose
The Safety Module is the highest authority in URIAH_TRADING.
It can veto entries and force flattening at any time.

Safety exists to prevent catastrophic outcomes, enforce operational integrity,
and stop trading when the system is not trustworthy.

Priority: **Safety > Volatility > HMM > Early Exit > Strategy**

---

## 2. Safety States (Authoritative)

### 2.1 safety_status
- `OK` — trading allowed (subject to other gates)
- `LOCKOUT` — no new entries allowed
- `FLATTEN` — immediate flatten required; entries blocked

Safety state changes must be logged as immutable events.

---

## 3. Safety Triggers (v1.0)
Safety triggers are grouped into categories.

### 3.1 Manual Controls
- Manual Disable (Admin): blocks new entries
  - result: `LOCKOUT`
  - reason: `manual_disabled`

- Manual Flatten (Admin confirmed): force flat
  - result: `FLATTEN`
  - reason: `manual_flatten_request`

Manual controls never bypass logging.

---

### 3.2 Communication Health (Python ↔ NT8)
Link health states:
- `LINK_OK`
- `LINK_DEGRADED`
- `LINK_LOST`
- `LINK_CORRUPT`

Rules:
- `LINK_DEGRADED` → `LOCKOUT` (block new entries)
- `LINK_LOST` → `LOCKOUT` immediately
- `LINK_CORRUPT` → `FLATTEN` immediately (safety-critical)

---

### 3.3 Reconciliation / Drift
Truth snapshots from NT8:
- `POSITION_STATUS`
- `ACCOUNT_STATUS`

Rules:
- Position mismatch (Python vs NT8 truth) → `FLATTEN`
- Account drift beyond tolerance → `LOCKOUT` (and `FLATTEN` if in position)

---

### 3.4 Contract Integrity
If `instrument.contract` is not the front/active intended contract:
- block new entries: `LOCKOUT`
- reason: `contract_not_front`

---

### 3.5 Guardrails (optional stubs in v1.0)
v1.0 may include stubs (log-only, not enforced) for:
- max daily loss / drawdown caps
- consecutive loss caps
- session time windows
These are out of scope unless explicitly activated.

---

## 4. Safety Outputs (Authoritative)

### 4.1 Entry Permission Override
If `safety_status != OK`:
- Python must return `ENTRY_PERMISSION = VETO`
- reason codes:
  - `safety_lockout`
  - `safety_flattening`
  - `manual_disabled`
  - `contract_not_front`
  - `link_lost`
  - `link_corrupt`

### 4.2 Flatten Command
If `safety_status == FLATTEN` and a position is open:
- Python must issue `EARLY_EXIT_NOW`
- trigger: `SAFETY`
- reason_code: one of:
  - `exit_safety_override`
  - `comms_fail_safe_flatten`
  - `position_mismatch_flatten`
  - `manual_flatten_request`

---

## 5. Event Logging (Mandatory)

Safety must write immutable events to the Safety Events store.

Minimum event fields:
- `ts_utc`
- `event_type`
- `severity` (INFO/WARN/CRITICAL)
- `safety_status_before`
- `safety_status_after`
- `reason_code`
- `instrument_root`
- `instrument_contract`
- `position_id` (nullable)
- `details_json` (free-form, structured)

All Safety decisions must be explainable from these events.

---

## 6. Telegram Notifications (Output-Only)
Safety must emit Telegram notifications for:
- entering LOCKOUT
- entering FLATTEN
- flatten executed result (ack/fill)
- link lost/corrupt and recovered
- position mismatch detected

Notifications must not influence decisions (one-way output).

---

## 7. Invariants
- Safety always overrides everything.
- Safety state changes are logged immutably.
- Dashboard “run control” cannot clear safety lockouts.
- Safety may flatten regardless of strategy state.

---

## 8. Status
Safety Module v1.0 — LOCKED
