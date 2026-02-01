# URIAH_TRADING — Logging Contract (v1)

## Purpose

This document defines the authoritative logging schema for URIAH_TRADING.

Logging exists to:
- Explain what happened and why
- Capture vetoes, belief decay, and system health
- Reconstruct every trade from womb to tomb
- Support post-trade analysis (not signal generation)
- Provide a forensic audit trail

All logs are:
- NDJSON (newline-delimited JSON)
- UTC timestamped
- Append-only
- Immutable once written

This contract is stable. Changes require a version bump.

---

## 1. Global Fields (Required on ALL Events)

Every log record (system or trade) MUST include the following fields.

| Field | Type | Required | Description |
|-----|-----|-----|-----|
| ts_utc | string | ✅ | UTC timestamp (ISO-8601). Auto-injected if missing |
| event_type | string | ✅ | Canonical event name |
| severity | enum | ✅ | DEBUG \| INFO \| WARN \| ERROR \| CRITICAL |
| module | string | ✅ | Emitting module |
| message | string | ✅ | Human-readable explanation |
| correlation_id | string | ✅ | Correlates related events |

### severity (enum)
Allowed values only:
- DEBUG
- INFO
- WARN
- ERROR
- CRITICAL

### ts_utc rules
- ISO-8601 UTC
- Z suffix required
- Auto-injected if missing
- Caller timestamps validated

Example:

2026-01-31T03:14:15.926Z

### Enforcement
A log record is invalid if:
- Any required field (except ts_utc) is missing
- severity is outside the enum
- event_type is empty

Invalid records MUST NOT be written.

---

## 2. Files & Formats

### 2.1 events.ndjson
System-level decisions and health.

Includes:
- startup / shutdown
- vetoes
- belief decay
- HMM regime changes
- lockouts
- errors

File:
logs/events.ndjson

---

### 2.2 trades.ndjson
Full trade lifecycle.

Includes:
- trade intent
- entry
- management
- exit
- settlement

Each trade must be fully reconstructable from this file alone.

File:
logs/trade.ndjson

---
### 2.3 heartbeat.txt

**Purpose:**  
Human-readable system liveness and health indicator.

This file exists to answer one question quickly:
> *Is the system alive and behaving normally?*

**Characteristics:**
- Plain text (not JSON)
- Overwritten on each update
- Intended for humans, scripts, and external monitors

**Contents (minimum):**
- Last heartbeat timestamp (UTC)
- Current system mode (RUNNING / LOCKED / ERROR)
- Last critical error (if any)

**Example contents:**

ts_utc=2026-01-31T09:45:00Z
status=RUNNING
last_error=NONE

**Rules:**
- Updated at a fixed interval (e.g. every 5 minutes)
- MUST be written even if no trades occur
- Failure to update is treated as a system fault

**File path:**

logs/heartbeat.txt



### 2.4 NDJSON format example
```json
{
  "ts_utc": "2026-01-31T03:14:15.926Z",
  "event_type": "SYSTEM_START",
  "severity": "INFO",
  "module": "SYSTEM",
  "message": "system started",
  "correlation_id": "SYS_20260131"
}

----

### Enforcement Rule

A log record is **invalid** if:
- Any required field is missing (except `ts_utc`)
- `severity` is not one of the allowed enum values
- `event_type` is empty or null

Invalid records MUST NOT be written.

## 3. Trade Identity & Lifecycle

All trade-related logging follows a **single lifecycle model**.
This allows every trade to be reconstructed deterministically.

### 3.1 trade_id
**Type:** string  
TYYYYMMDD_NNNN
**Description:** Unique identifier for a trade.

Rules:
- Generated once at trade intent
- Stable for the entire lifecycle
- Used in both `events.ndjson` and `trades.ndjson`

Example:


T20260131_0007

### 3.2 correlation_id

**Type:** string  
**Description:** Identifier used to correlate multiple events belonging to the same decision chain, session, or system run.

Rules:
- Present on all events (system + trade)
- Stable across a linked sequence of events
- May be session-scoped (`SYS_YYYYMMDD`) or trade-scoped, but must be consistent within the chain

Example:

SYS_20260131
T20260131_0007
### 3.3 Required Lifecycle Events

The following `event_type` values are mandatory for trade tracking:

- TRADE_INTENT
- ENTRY_VETO
- TRADE_ENTRY
- TRADE_MANAGING (o..N)
- TRADE_EXIT
- TRADE_SETTLED

Each event MUST reference:
- `trade_id`
- `correlation_id`

---

### 3.4 Single-Position Rule

At most **one active trade** may exist at any time.

Rules:
- No overlapping `ENTERED` states
- New `TRADE_INTENT` is rejected if an active trade exists
- Violations are logged as `CRITICAL` severity

## 4. Entry Veto Logging

Every rejected trade setup MUST be logged.
A veto is as important as a trade.

### 4.1 ENTRY_VETO event

**event_type:** ENTRY_VETO  
**severity:** INFO  
**module:** ENTRY_GATE

This event records **why a trade was not taken**, even though a setup existed.

---

### 4.2 Required Fields for ENTRY_VETO

Each ENTRY_VETO record MUST include:

- `trade_id`
- `correlation_id`
- `veto_reason_code`
- `veto_reason_detail`

---

### 4.3 veto_reason_code (enumerated)

The following codes are **authoritative**.
New codes require a contract update.

| Code | Description |
|----|-------------|
| HMM_DIRECTION | HMM disallowed trade direction |
| HMM_REGIME | Market regime not permitted |
| TIME_LOCKOUT | Session time restriction |
| DAILY_DD | Daily drawdown limit reached |
| TIME_DEBT | Time-to-recovery filter |
| VELOCITY | Velocity / acceleration gate failed |
| VOLUME | Volume confirmation failed |
| MICROSTRUCTURE | L2 / microstructure check failed |
| EXPECTANCY | Expected R / time-to-TP failed |
| SINGLE_POSITION | Existing active trade |
| SYSTEM_HEALTH | System health filter |
| MANUAL | Operator intervention |

---

### 4.4 Purpose of Veto Logging

ENTRY_VETO logs enable analysis of:
- missed opportunities
- hostile market conditions
- over-filtering
- regime mismatch
- filter redundancy

A high veto rate is **not** an error.
It is diagnostic information.

## 5. Trade Entry Logging

A trade entry is logged only after an order is accepted and a position exists.

### 5.1 TRADE_ENTRY event

**event_type:** TRADE_ENTRY  
**severity:** INFO  
**module:** EXECUTION_MANAGER

This event marks the **official start** of a trade lifecycle.

---

### 5.2 Required Fields for TRADE_ENTRY

Each TRADE_ENTRY record MUST include:

- `trade_id`
- `correlation_id`
- `instrument`
- `direction` (LONG | SHORT)
- `contracts`
- `entry_price`
- `entry_timestamp`
- `initial_stop_price`
- `initial_target_price`
- `risk_points`
- `risk_usd`
- `expected_r_multiple`
- `expected_time_to_target_sec`

---

### 5.3 Context Fields (Recommended)

These fields are not used for execution logic but are logged for analysis:

- `hmm_regime`
- `hmm_direction`
- `hmm_confidence`
- `volatility_state`
- `velocity_state`
- `time_of_day_bucket`

---

### 5.4 Entry Attribution

TRADE_ENTRY establishes the **baseline belief** for the trade.

All later belief decay, exits, and attribution are measured
relative to this event.

## 6. Trade Management & Belief Decay Logging

Trade management events record **in-trade evolution** of belief, risk, and control.
They do not create signals; they explain decisions.

### 6.1 TRADE_MANAGING event

**event_type:** TRADE_MANAGING  
**severity:** INFO  
**module:** EXECUTION_MANAGER

Emitted whenever a meaningful management action or belief update occurs.

Examples:
- stop moved
- target adjusted
- trailing logic engaged
- belief score updated
- HMM state changed during trade

---

### 6.2 Required Fields for TRADE_MANAGING

Each TRADE_MANAGING record MUST include:

- `trade_id`
- `correlation_id`
- `current_price`
- `elapsed_time_sec`
- `mfe_points`
- `mae_points`
- `unrealized_pnl_usd`

---

### 6.3 Belief State Fields

These fields quantify **ongoing belief** in the trade:

- `belief_score` (0.0 – 1.0)
- `belief_trend` (IMPROVING | STABLE | DECAYING)
- `belief_decay_reason` (optional)

---

### 6.4 Regime & Structure Updates

If market state changes during a trade, the following MUST be logged:

- `hmm_regime_current`
- `hmm_direction_current`
- `hmm_confidence_current`

A **directional flip against the trade** is a critical belief event.

---

### 6.5 Purpose

These logs enable:
- diagnosis of early exits
- analysis of time / velocity failure
- validation of belief-based exits
- refinement of management rules

No trade management decision may occur **without a corresponding log record**.

## 7. Trade Exit & Outcome Logging

Trade exits record **why** a position was closed and **what resulted**.
Exit quality is as important as entry quality.

### 7.1 TRADE_EXIT event

**event_type:** TRADE_EXIT  
**severity:** INFO  
**module:** EXECUTION_MANAGER

This event marks the **end of market exposure**.

---

### 7.2 Required Fields for TRADE_EXIT

Each TRADE_EXIT record MUST include:

- `trade_id`
- `correlation_id`
- `exit_reason_code`
- `exit_price`
- `exit_timestamp`
- `realized_pnl_usd`
- `r_multiple_realized`
- `hold_time_sec`

---

### 7.3 exit_reason_code (enumerated)

The following codes are **authoritative**:

| Code | Description |
|----|-------------|
| TARGET_HIT | Profit target reached |
| STOP_HIT | Catastrophic stop hit |
| BELIEF_DECAY | Belief fell below threshold |
| TIME_VELOCITY | Time / velocity condition failed |
| RETRACEMENT | Retracement logic triggered |
| REGIME_FLIP | HMM flipped against trade |
| TIME_LOCKOUT | Session end / forced flat |
| MANUAL | Operator intervention |
| ERROR | System error |

---

### 7.4 TRADE_SETTLED event

**event_type:** TRADE_SETTLED  
**severity:** INFO  
**module:** SYSTEM

This event finalizes attribution and analytics.
It occurs **after** TRADE_EXIT.

---

### 7.5 Required Fields for TRADE_SETTLED

Each TRADE_SETTLED record MUST include:

- `trade_id`
- `correlation_id`
- `gross_pnl_usd`
- `fees_usd`
- `net_pnl_usd`
- `margin_required_usd`
- `points_captured`
- `session_points_travelled`

---

### 7.6 Purpose

Exit and settlement logs enable:
- assessment of stop effectiveness
- identification of premature exits
- transaction cost analysis
- capital efficiency measurement

## 8. System Health & Lockouts

System health logging captures **when and why trading is restricted or halted**.
These events protect capital, time, and system integrity.

### 8.1 SYSTEM_HEALTH event

**event_type:** SYSTEM_HEALTH  
**severity:** INFO | WARN | CRITICAL  
**module:** SYSTEM

Emitted whenever system health state changes.

Examples:
- data feed degradation
- execution latency
- module failure
- recovery from error

---

### 8.2 LOCKOUT_TRIGGERED event

**event_type:** LOCKOUT_TRIGGERED  
**severity:** WARN | CRITICAL  
**module:** RISK_MANAGER

This event indicates that trading has been **paused or stopped**.

---

### 8.3 Required Fields for Lockout Events

Each LOCKOUT_TRIGGERED record MUST include:

- `lockout_type`
- `lockout_reason`
- `lockout_scope` (SESSION | DAY | SYSTEM)
- `lockout_threshold`
- `lockout_current_value`

---

### 8.4 lockout_type (enumerated)

| Type | Description |
|----|-------------|
| TIME_OF_DAY | First 15 minutes / session end |
| DAILY_DRAWDOWN | High-water-mark drawdown |
| LOSING_STREAK | Losing streak escalation |
| MONTE_CARLO | MC probability breach |
| TIME_DEBT | Time-to-recovery escalation |
| SYSTEM_HEALTH | Infrastructure failure |

---

### 8.5 HEARTBEAT updates

The heartbeat file MUST be updated:
- on system start
- on system shutdown
- at a fixed interval during operation

Heartbeat includes:
- last_update_utc
- system_mode (RUNNING | PAUSED | STOPPED)
- last_critical_error (optional)

---

### 8.6 Purpose

Health and lockout logs enable:
- forensic diagnosis of downtime
- validation of risk governance
- confidence in unattended operation




















