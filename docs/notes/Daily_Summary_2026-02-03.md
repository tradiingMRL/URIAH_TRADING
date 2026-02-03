## Future Build Direction — Read-Only Monitoring Portal

### Objective
Provide a simple, secure, read-only portal for monitoring system performance, health, and behaviour without exposing any execution or control capability.

### Design Principles
- **Strict separation of concerns**
  - Execution layer (trading engine) is fully isolated from any UI or portal
  - Portal operates in read-only mode against SQLite (no writes, no commands)
- **“Look, no touching” guarantee**
  - No trade execution
  - No parameter changes
  - No system state mutation
- **Single source of truth**
  - Portal reads only from SQLite (post-ingestion data)
  - No direct dependency on live trading processes

### Access & Roles (Planned)
- **Admin (Owner)**
  - Full visibility
  - Diagnostics, gate statistics, early exit analysis
  - System health and exception reporting
- **Viewer (Read-only)**
  - Equity curve
  - Trade list and summaries
  - Daily/weekly performance
  - High-level system status indicators
  - No configuration, no controls

### Security Model
- Password-protected access
- Role-based views
- Portal process runs independently from trading engine
- Failure or misuse of portal cannot impact execution layer

### User Experience Goal
- One-click desktop shortcut or local URL
- Immediate visibility into:
  - Today’s performance
  - System state (healthy / degraded / locked)
  - Trade activity summary
- Suitable for sharing with trusted observers (e.g. family) without operational risk

### Implementation Timing
- **Deferred until after live logging is stable**
- No dependency on this feature for trading correctness
- Enabled by existing logging, schema, and SQLite architecture
## Future Build Direction — Read-Only Web Dashboard (Locked)

### Decision (Locked)
The monitoring dashboard will be implemented as a web-based, read-only interface hosted on the VPS and backed by SQLite.

Primary access device: iPad  
Secondary access: desktop browser (optional)

### Rationale
- RDP access on iPad is ergonomically poor for monitoring
- Web UI provides fast, touch-friendly read-only access
- Strict separation between execution and observation
- Safe sharing with trusted viewers (“look, no touching”)

### Design Constraints
- Dashboard is read-only by design
- Reads from SQLite only (no writes, no commands)
- Runs as a separate process from NT8
- Failure or misuse cannot impact execution
- No public exposure required (local / tunneled access only)

### Scope (Deferred)
- Equity curve
- Trade lifecycle drill-down
- Gate pass/fail summaries
- System health & exception indicators
- Daily / weekly summaries

### Explicitly Out of Scope
- Trade execution
- Parameter changes
- Strategy control
- Live debugging
- Data mutation

### Implementation Timing
- Deferred until live trade logging is stable
- Enabled by existing schema, ingestion, and lifecycle design
# URIAH_TRADING — Build Roadmap & Schedule of Work (v1.0)

Purpose  
This document captures all non-strategy and strategy work items required to build, operate, and govern the URIAH_TRADING system safely.  
It exists to prevent infrastructure, platform, and operational risks from being forgotten or treated informally.

This roadmap is a living document, reviewed weekly and updated deliberately.

---

## Status Legend
- ⏳ Planned
- 🔧 In Progress
- ✅ Locked / Completed
- 🚫 Explicitly Rejected / Will Not Do

---

## 1. Infrastructure & Operating System (Windows / VPS)

Risk Type: Existential  
If these fail, the system fails regardless of strategy quality.

### Items
- ⏳ Define Windows Update policy (manual approval, weekend-only)
- ⏳ Disable forced restarts during trading hours
- ⏳ Define VPS reboot / auto-restart behaviour
- ⏳ Ensure NinjaTrader auto-starts after reboot
- ⏳ Confirm system clock sync (UTC authoritative)
- ⏳ Disk space monitoring and alert thresholds
- ⏳ Internet quality monitoring (latency / packet loss)
- ⏳ Define minimum acceptable connectivity thresholds
- ⏳ Task Scheduler rules for:
  - NT startup
  - Python ingestion jobs
  - Health checks
- ⏳ Antivirus / Defender exclusions for NT, data, logs

---

## 2. Platform Setup — NinjaTrader 8

Risk Type: Operational  
Misconfiguration here causes silent, hard-to-diagnose failures.

### Items
- ✅ Multi-user mode enabled (required for connection configuration)
- ✅ Plug-in mode explicitly disabled
- ⏳ Workspace auto-load configuration
- ⏳ Strategy auto-load vs strategy arm separation
- ⏳ Explicit strategy DISARMED state on startup
- ⏳ Prevent auto-trading on reconnect
- ⏳ NT restart behaviour after crash
- ⏳ Log retention and rollover policy
- ⏳ NT log parsing rules (for health monitoring)

---

## 3. Broker & Connectivity — Rithmic

Risk Type: Execution / Market Access

### Items
- ✅ Rithmic paper trading account established
- ✅ NT ↔ Rithmic connection configured
- ⏳ Explicit SAFE / NOT SAFE definition (Primary + Price Feed)
- ⏳ Connection state logging (health events)
- ⏳ Lockout policy on NOT SAFE
- ⏳ Force-flat policy on NOT SAFE
- ⏳ Reconnect behaviour governance (no auto-resume trading)
- ⏳ Server-side protective order verification (SL/TP)
- ⏳ Gateway selection locked (Chicago)
- ⏳ Credential expiry / re-auth handling

---

## 4. Strategy Governance (System-Level Rules)

Risk Type: Logical / Financial

### Items
- ⏳ One-position-at-a-time enforcement
- ⏳ Strategy loaded ≠ strategy armed separation
- ⏳ Manual vs rule-based arming decision
- ⏳ Overnight trading rules
- ⏳ Session boundaries and behaviour
- ⏳ Drawdown-based lockouts
- ⏳ Capital-at-risk envelope definition
- ⏳ Behaviour on restart with open positions
- ⏳ Explicit force-flat precedence over all other logic

---

## 5. Data, Logging & Review

Risk Type: Learning / Audit / Governance

### Items
- ✅ Data logging schema defined
- ✅ SQLite schema defined
- ⏳ Connection health event logs
- ⏳ Lockout event logging
- ⏳ Daily summary generation
- ⏳ Weekly review & action summary process
- ⏳ Python ingestion verification jobs
- ⏳ KPI and survivability metrics definition
- ⏳ Dashboard (read-only, web-based) — future
- ⏳ Access control (read-only for observers)

---

## 6. Backtesting & Capital Survivability (Future Phase)

Risk Type: Financial Sustainability

### Items
- ⏳ Peak drawdown analysis
- ⏳ Worst-case overnight sequence modelling
- ⏳ Minimum survivable account size
- ⏳ Commission & slippage stress tests
- ⏳ Capital scaling rules (only after validation)

---

## Governance Rules for This Roadmap

- Only one domain is actively worked on at a time
- Changes require explicit agreement and version bump
- Weekly review:
  - Move items between statuses
  - Define next-week focus
- No strategy logic work proceeds unless:
  - Infrastructure and connectivity items are locked or mitigated

---

URIAH_TRADING — Daily Summary
Date: 2026-02-03 (AU)

==================================================

1) What was completed today
---------------------------

- SQLite live database initialised and validated
- Trade events ingestion pipeline working end-to-end
- Ingest idempotency confirmed (hash-based)
- Connection health logging added (connection_events)
- Safety events table added (safety_events)
- Controller heartbeat implemented and verified
- Force-flat + lockout policy implemented and logged
- Reset mechanism via flag file implemented
- Decision tree documented and committed
- Volatility gate finalised (velocity/time-based, non-ATR)
- System outline committed to Git

--------------------------------------------------

2) What is now LOCKED
---------------------

- Single-position only (no scale-ins)
- No order modification allowed under any circumstances
- Connection loss or corruption → force flat + lockout
- Volatility gate is veto/weighting only (never directs trades)
- HMM and volatility are regime/context only
- Python is control/monitoring layer, not execution

--------------------------------------------------

3) Known open items (not started)
---------------------------------

- A5 completion (remaining safety state handling)
- HMM global state design + logging
- Volatility statistics gate (separate from HMM)
- Trade lifecycle summary report (per-trade rollup)
- Dashboard (web-based, read-only, multi-user)
- NT8 execution module hardening
- Rithmic production connection hardening

--------------------------------------------------

4) Decisions made today
-----------------------

- Web-based dashboard confirmed (iPad-friendly)
- NT8 = execution only
- Python = orchestration, safety, logging
- Rithmic = data + execution feed
- No mid-trade decision authority for HMM or volatility

--------------------------------------------------

5) Next planned focus
---------------------

- Finish A5 (safety state machine)
- Then move to HMM Global State design

==================================================
End of Summary

Version: v1.0  
Status: Active  
Review Cadence: Weekly