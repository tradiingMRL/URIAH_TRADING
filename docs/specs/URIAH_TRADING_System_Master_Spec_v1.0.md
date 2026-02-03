# URIAH_TRADING — System Master Spec v1.0 (LOCKED)

## 1. Purpose
This document is the single authoritative index for the URIAH_TRADING system design.
It defines the system’s purpose, invariants, module boundaries, and how the components
fit together.

All module specs referenced here are authoritative. This file exists so the user can
point to one document and say: “This is my system.”

---

## 2. System Summary (One Paragraph)
URIAH_TRADING is a safety-first, permission-gated trading system where NinjaTrader 8 (NT8)
executes System A (breakout) and System B (mean reversion), while a Python orchestrator
provides safety governance, volatility gating, HMM regime context, and binary early-exit
decisions. The system enforces single-position-at-a-time, has no trade-mechanic mutation
post-entry (no trailing/BE/partials/max-hold adjustments), and uses audit-grade logging,
reconciliation, and observability (dashboard + Telegram notifications).

---

## 3. Non-Negotiable Invariants (Constitution)
These rules cannot be broken by any implementation:

1) Safety overrides everything
- Safety may block entries or force flattening at any time.

2) HMM must never direct trades
- HMM may veto entry and trigger exit reviews only.

3) Early Exit is binary
- Only outcomes: `PERSIST` or `EXIT_EARLY`.

4) No trade-mechanic mutation post-entry
- No changes to stop distance, TP distance, trailing, break-even, max-hold, partial exits.
- Trades are either open unchanged or closed.

5) Single position at a time
- Across System A and System B combined.

6) Instrument resolution is mandatory and contract-aware
- No hard-coded expiry months anywhere.
- All messages/logs include root + active contract.

7) Explainability is mandatory
- Every gating decision and exit decision must be explainable from logs.

---

## 4. Architecture Overview

### 4.1 Control Plane vs Execution Plane
- Control Plane (Python): Safety, Volatility, HMM, Early Exit, logging, notifications.
- Execution Plane (NT8): detects setups, requests permission, executes entries/exits.

### 4.2 Decision Priority Order (Fixed)
**Safety > Volatility > HMM > Early Exit > Strategy**

### 4.3 Data Flow (High Level)
1) NT8 detects a setup → sends `ENTRY_INTENT`
2) Python evaluates gates → replies `ENTRY_PERMISSION (ALLOW|VETO)`
3) If ALLOW, NT8 executes entry and reports fills via `FILL_REPORT`
4) If trigger occurs (HMM transition, EVWAP touch, box/zone re-entry), Python runs Exit Review
5) If Exit Review decides EXIT_EARLY → Python sends `EARLY_EXIT_NOW`
6) NT8 executes exit immediately and reports via `EXIT_ACK` + `FILL_REPORT`
7) Logs/DB feed dashboard and Telegram notifications

---

## 5. Module Index (Authoritative Specs)

### 5.1 Global Gates & Core Risk Control
- Volatility Module:
  - `docs/specs/URIAH_TRADING_Volatility_Module_v1.0.md`

- HMM Global Regime Module:
  - `docs/specs/URIAH_TRADING_HMM_Global_Regime_Module_v1.0.md`

- Early Exit Engine:
  - `docs/specs/URIAH_TRADING_Early_Exit_Engine_v1.0.md`

### 5.2 Interfaces & Instrument Governance
- Message Contracts:
  - `docs/specs/URIAH_TRADING_Message_Contracts_v1.0.md`

- Instrument Resolution:
  - `docs/specs/URIAH_TRADING_Instrument_Resolution_v1.0.md`

### 5.3 Execution Layer
- NT8 Execution Design:
  - `docs/specs/execution/URIAH_TRADING_NT8_Execution_Design_v1.0.md`

### 5.4 Observability Layer
- Dashboard & Observability Design:
  - `docs/specs/observability/URIAH_TRADING_Dashboard_Observability_Design_v1.0.md`

### 5.5 Safety Event Pipeline (Status)
Safety event pipeline artifacts exist but are not yet committed as a locked module spec:
- `tools/python/safety_event_logger.py` (untracked)
- `tools/sqlite/add_safety_events_table_v1.0.sql` (untracked)

Policy:
- Safety module spec + code + DB migration will be committed as an atomic Safety v1.0 release.

---

## 6. Strategy Scope (v1.0)

### 6.1 System A (Breakout, NT8 execution)
- NT8 identifies breakout setup
- Python gates entry (Safety + Volatility + HMM compatibility)
- Post-entry mechanics are fixed (catastrophic SL + fixed TP)
- Early exit only via binary Exit Review

### 6.2 System B (Mean Reversion, NT8 execution)
- NT8 identifies mean-reversion setup
- Python gates entry (Safety + Volatility + HMM compatibility)
- Post-entry mechanics are fixed (catastrophic SL + fixed TP)
- Early exit only via binary Exit Review

---

## 7. Run Control (Operational On/Off)

### 7.1 Trading Enable Switch (Admin-Controlled)
A manual run control may exist (e.g., set by Admin via dashboard):
- When disabled, Python returns `ENTRY_PERMISSION = VETO` with reason `manual_disabled`
- This blocks new entries but does not alter existing trades unless explicitly requested

### 7.2 Flatten Now (Admin, Confirmed Action Only)
A separate Admin-only action may request immediate flatten:
- Executed via `EARLY_EXIT_NOW` with trigger `SAFETY` and reason `manual_flatten_request`
- Must require explicit confirmation (anti-fat-finger)

### 7.3 Safety Lockout Supremacy
- Manual “ON” cannot override Safety LOCKOUT/FLATTEN states
- Lockouts clear only by Safety policy and/or operator investigation

---

## 8. Reconciliation & Anti-Tamper (Operational Integrity)

### 8.1 NT8 Truth Snapshots
NT8 periodically reports:
- `ACCOUNT_STATUS`
- `POSITION_STATUS`

### 8.2 Drift Handling
If Python detects mismatch:
- Position drift → Safety escalation (default: flatten)
- Account drift beyond tolerance → LOCKOUT + investigate

### 8.3 Comms Loss Fail-Safe
If NT8 loses Python link beyond dwell threshold:
- No new entries
- Optional fail-safe flatten of open position (policy defined in NT8 execution design)

---

## 9. Logging & Auditability (Minimum Standard)
The system must persist logs sufficient to reconstruct:
- gate decisions (allow/veto + reason codes)
- volatility state and transitions
- HMM state, confidence, margin, transitions
- early exit triggers, decisions, reasons
- fills (requested vs filled, signed slippage, latency)
- safety events
- instrument root + contract on every record

All logs must be:
- append-only
- timestamped (UTC)
- versioned (module versions recorded where applicable)

---

## 10. Observability & Notifications
- Dashboard is read-only for system logic; can optionally expose Admin run control.
- Telegram notifications (output-only) cover:
  - lockouts / flatten events / comms loss-recovery / contract mismatch
  - daily performance summary
  - optional heartbeat

---

## 11. Release Discipline (How “Finished Code” Lives)
Source of truth is Git.

Production rules:
- Production runs only from a tagged release (e.g., `v1.0.0`)
- Python logs and Telegram heartbeat should include commit hash + mode + trading-enabled status
- Rollback is performed by checking out an earlier tag and restarting the orchestrator

No “mystery production code” outside Git is permitted.

---

## 12. Status
**URIAH_TRADING System Master Spec v1.0 — LOCKED**

This document completes the system design index and establishes the authoritative
reference point for implementation and operations.

