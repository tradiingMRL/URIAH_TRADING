# Connection Safety Policy v1.0
URIAH_TRADING

## Purpose
This document defines the **mandatory connection safety rules** governing
all trading activity when using NinjaTrader 8 with a Rithmic data/execution
connection.

The objective is to ensure the system **fails safe**, never trades in an
undefined connectivity state, and produces a complete audit trail of all
connection-related events.

This policy applies to **all systems** (System A, System B, future systems).

---

## Definitions

### Connection Components
NinjaTrader reports Rithmic connectivity using two independent components:

- **Primary connection**
- **Price feed**

Both components must be healthy for trading to be permitted.

---

## Canonical Connection States

### SAFE
The system is considered **SAFE** only when:

- There is **no active NOT SAFE condition**
- The most recent connection state is not Connecting, Disconnecting, or Disconnected
- No broker-enforced disconnect or authorization error is active

> Note: NinjaTrader does **not reliably emit an explicit
> “Primary=Connected Price feed=Connected” log line**.
> Therefore SAFE is defined **by exclusion**, not by waiting for a positive signal.

---

### NOT SAFE
The system is considered **NOT SAFE** if **any** of the following conditions
are observed (verbatim from NT logs):

Primary connection=Connecting Price feed=Connecting
Primary connection=Disconnecting Price feed=Disconnecting
Primary connection=Disconnected Price feed=Disconnected
Disconnect enforced by broker or 2nd login to the same account
There are no email share services defined (ignored for trading)
Authorization / permission errors
Any connection-related error emitted by NinjaTrader

NOT SAFE is triggered if **either** Primary or Price Feed is not healthy.

---

## Lockout Policy

### Rule 1 — Entry Gating
- If the system is NOT SAFE at the moment of an entry decision:
  - **All new trades are denied**
  - Entry decision is logged as DENY with reason `CONNECTION_NOT_SAFE`

---

### Rule 2 — Post-Entry Behaviour (Hard Rule)
If the system transitions from SAFE → NOT SAFE **at any time**:

> **The system must immediately FORCE FLAT, regardless of trade state.**

There are **no exceptions** for:
- Trade profitability
- Distance to stop or target
- Strategy type
- Regime state
- Time in trade

This rule is absolute.

---

## FORCE FLAT Behaviour

### Step 1 — Immediate Action
Upon detecting NOT SAFE:
1. Set `lockout_active = 1`
2. Set `lockout_reason = CONNECTION_NOT_SAFE`
3. Initiate **FORCE FLAT**

FORCE FLAT must:
- Attempt to flatten all open positions immediately
- Use the most direct and robust mechanism available (account-level flatten
  and/or market exit orders)

---

### Step 2 — Failure Handling
If flattening cannot be confirmed due to connection degradation:
- Enter `FLATTEN_PENDING` state
- Continue attempting flatten on reconnect
- Do not allow any other trading actions

---

### Step 3 — Reconnect Behaviour
When connectivity returns:
- FORCE FLAT is retried until position size = 0
- Lockout remains active
- Trading does **not** resume automatically

Lockout may only be cleared by:
- Explicit operator action
- Or a defined session reset policy (to be specified later)

---

## Logging Requirements

### Connection Health Log
Append-only CSV files written to:

# Connection Safety Policy v1.0  
URIAH_TRADING

---

## Purpose

Protect capital by enforcing **non-negotiable safety rules** when market
connectivity, broker state, or execution integrity is compromised.

This policy **overrides all strategy logic** (System A, System B, or any
future systems).

If safety cannot be guaranteed, the system must **exit risk immediately**
and **cease trading until manually reset**.

---

## Scope

This policy applies to:
- All live and paper trading
- All systems (A, B, future systems)
- All market conditions
- All times (pre-entry and post-entry)

---

## Global Trading Constraints (Always-On)

These constraints apply **at all times**, regardless of SAFE / NOT SAFE state.

### G1 — Fixed Position Size
- No scale-ins
- No scale-outs (except full exit / flatten)
- No pyramiding
- Exactly **one entry → one exit** lifecycle per trade

### G2 — No Order Modifications
- No cancel/replace of protective orders once attached
- No moving stop-loss
- No changing target
- No discretionary order management

**Permitted actions only:**
- Place initial entry with attached SL/TP
- FORCE FLAT (cancel orders + close position)

---

## Definitions

### SAFE
All of the following must be true:
- Primary broker connection = Connected
- Price feed = Connected
- No broker-enforced disconnect
- No authorization / duplicate-login errors
- Controller / Python link is healthy
- Connection state is consistent and certain

### NOT SAFE
If **any** of the above conditions is violated.

---

## Safety Signals (Inputs)

### Execution / Broker Signals
Source: NinjaTrader connection state + broker messages

- Primary connection state
- Price feed state
- Authorization failures
- Broker-enforced disconnects
- Duplicate login detection
- Inconsistent or unknown connection state

Logged to:
- `connection_events`

---

### Controller / Python Link Safety

Execution must have a reliable link to the controller / logging layer.

**PY_LINK_SAFE = true** when:
- Local log writes succeed (CSV / SQLite append)
- Controller heartbeat is fresh within threshold
- IPC / file-based signaling (if used) is responsive

**PY_LINK_NOT_SAFE = true** when:
- Log writes fail (I/O error, permissions, disk full)
- Heartbeat is stale beyond threshold
- Controller process is not running when required
- IPC channel is disconnected or unresponsive

**Policy rule:**  
`PY_LINK_NOT_SAFE` is treated as **NOT SAFE**.

---

## Hard Rules (Non-Negotiable)

### Rule S1 — Any Connection Loss or Corruption → NOT SAFE
The system is **NOT SAFE** if **any** of the following occur:
- Primary connection is not Connected
- Price feed is not Connected
- Broker-enforced disconnect or authorization failure
- Connection state becomes uncertain or inconsistent
- Controller / Python link is NOT SAFE

---

### Rule S2 — NOT SAFE → Force Flat Immediately
If NOT SAFE is detected **at any time**:
- 🔴 Cancel all working orders
- 🔴 Flatten all open positions immediately
- 🔴 Enter LOCKOUT state

This rule applies regardless of:
- unrealized PnL
- proximity to TP
- system confidence
- time remaining in trade
- market conditions

Safety always overrides strategy.

---

### Rule S3 — Lockout Until Manual Reset
While LOCKOUT is active:
- ❌ No new orders of any kind are permitted
- ❌ Trading does not resume automatically
- ✅ Trading resumes **only** after an explicit manual reset

---

## Logging Requirements

On detection of NOT SAFE:
- Emit `connection_events` row
- Emit `trade_events` row with:
  - `event_type = FORCE_FLAT`
  - `exit_reason_code = CONNECTION_NOT_SAFE`
- Emit LOCKOUT event
- Persist all details for audit and post-analysis

---

## Design Principles (Intentional)

- Safety logic is **independent** of strategy logic
- Strategy code may request actions; safety code may veto them
- Conservative bias is intentional
- False positives are preferred over false negatives
- No grace periods in v1.0

---

## Future Extensions (Not v1.0)

- Grace periods with decay
- Redundant feed confirmation
- Auto-unlock after sustained SAFE period
- Partial flatten rules
- Multi-broker quorum logic

---

## Version
- Version: 1.0  
- Status: Active  
- Change control: Git-tracked only