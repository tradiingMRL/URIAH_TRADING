# URIAH_TRADING — Dashboard & Observability Design v1.0 (LOCKED)

## 1. Purpose
This document defines the authoritative design boundaries for the URIAH_TRADING
Dashboard and Observability layer.

The dashboard exists to provide:
- auditability
- explainability
- monitoring
- performance and risk reporting

The dashboard is strictly read-only.
It must never influence trading decisions or execution.

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Observe Only
- No control actions
- No parameter tuning
- No live overrides
- No execution hooks

### 2.2 Explainability Over Aesthetics
- Every decision must be traceable to logs
- Reason codes and state transitions must be visible
- Visuals must prioritise clarity over decoration

### 2.3 Separation From Execution
- Dashboard consumes stored data only
- No direct connection to NT8 execution
- No direct connection to live decision engines
- Dashboard must be replaceable without changing trading logic

---

## 3. Data Sources (Read-Only)

The dashboard reads exclusively from persisted data sources:

- volatility logs
- HMM state logs
- HMM transition logs
- early exit logs
- entry permission / veto logs
- fill & slippage logs (`FILL_REPORT`)
- safety event logs
- optional NT8 truth snapshots:
  - `ACCOUNT_STATUS`
  - `POSITION_STATUS`

Preferred long-term store:
- SQLite (append-only tables)

Fallback / interim store:
- CSV logs (append-only)

No dashboard component may write to these sources.

---

## 4. Instrument Resolution (Mandatory)

All dashboard views must be contract-aware.

Every record must include:
- `instrument_root` (e.g. MES)
- `instrument_contract` (e.g. MES 06-26)

Dashboard views must:
- default to a single contract
- prevent silent mixing of contracts
- allow explicit cross-contract comparison only when selected

---

## 5. Dashboard Scope (v1.0)

### 5.1 System Health Panel
Displays near-live operational status:

- Python orchestrator status: RUNNING / DEGRADED / DOWN
- NT8 connection health
- Last heartbeat timestamps
- Current instrument (root + contract)
- Link state:
  - LINK_OK
  - LINK_DEGRADED
  - LINK_LOST
  - LINK_CORRUPT
- Global gate snapshot:
  - Safety status
  - Volatility state (HOT / NORMAL / INERT)
  - HMM state, confidence, margin
- Current position summary:
  - FLAT / IN_POSITION
  - strategy (System A / System B)
  - side, quantity, average price
  - time in trade

---

### 5.2 Gate Decisions Panel
Explains *why trades did or did not occur*:

- Entry intents over time
- Allowed vs vetoed entries
- Veto counts by reason_code
- Single-position rule veto events
- Contract mismatch veto events

---

### 5.3 Regime Panel
Visualises market state context:

- Volatility state timeline
  - HOT / NORMAL / INERT bands
- HMM state timeline
  - TREND / MEAN_REVERT / CHAOTIC / DEAD
- State transitions and dwell times
- HMM confidence and margin plots

---

### 5.4 Early Exit Panel (Core Risk Control)
Explains trade exits and protections:

- Exit review triggers:
  - HMM_TRANSITION
  - EVWAP_TOUCH
  - BOX_REENTRY
  - ZONE_REENTRY
- Decisions:
  - PERSIST
  - EXIT_EARLY
- Reason code distribution
- Time-in-trade at review
- Time–velocity decay metrics at review
- Logistic regression `p_continue` values (EVWAP_TOUCH only)

---

### 5.5 Slippage & Execution Quality Panel
Monitors execution performance:

- Entry slippage distribution
- Exit slippage distribution
- Slippage grouped by exit reason:
  - TP
  - SL
  - EARLY_EXIT
  - SAFETY
- Order latency:
  - submit → fill time
- Slippage outliers (flagged only; no control action)

---

### 5.6 Performance Panel (High Level)
Informational performance summaries:

Per strategy (A / B) and combined:
- trade count
- win rate (informational)
- expectancy / R (if computed)
- profit factor (if computed)
- average hold time
- MAE / MFE (if available)
- daily / weekly / monthly summaries

All performance views must respect contract filters.

---

## 6. Reconciliation & Drift Monitoring (Mandatory)

### 6.1 Position Drift
Dashboard must surface alerts if:
- Python believes FLAT but NT8 reports IN_POSITION
- Python believes IN_POSITION but NT8 reports FLAT

---

### 6.2 Account Drift
Dashboard must surface alerts if:
- NT8-reported balance or equity deviates from Python-recorded values beyond tolerance

Dashboard alerts are informational only.
Corrective actions are governed by Safety policy.

---

## 7. Security & Integrity

- Dashboard access is read-only
- No credentials embedded in client-side code
- All inputs validated defensively
- Dashboard cannot write to logs, databases, or execution layers

---

## 8. Implementation Notes (Out of Scope for v1.0)

This design does not mandate a specific UI framework.

Implementation options may include:
- Grafana
- Custom web application

v1.0 requires only that:
- data is parseable
- data is contract-aware
- views defined in Section 5 exist

---

## 9. Invariants (Cannot Be Broken)

- Dashboard never influences trading logic
- Dashboard is replaceable without system changes
- Contract-aware analytics are mandatory
- Explainability is mandatory

---

## 10. Design Philosophy

- Governance over optimisation
- Explanation over persuasion
- Stability over novelty
- Auditability over convenience

---

## 11. Access, Security, and Delivery (v1.0)

### 11.1 Delivery
The dashboard must be web-based and mobile responsive.
It must be usable on iPad (Safari / WebKit).

---

### 11.2 Authentication
The dashboard must be password protected and served over HTTPS.

Recommended deployment:
- Grafana behind a reverse proxy (Caddy or Nginx)
- Reverse proxy terminates TLS

---

### 11.3 Multi-User & Permissions (RBAC)
The dashboard must support multiple users with role-based access control.

Minimum roles:
- Admin: manage users and permissions; view all
- Operator: view all operational panels
- Viewer: read-only access to high-level dashboards
- Auditor: read-only access to immutable logs and exports

---

### 11.4 Read-Only Guarantee
Dashboard access must be read-only with respect to:
- NT8 execution layer
- Python decision engines (Safety, Volatility, HMM, Early Exit)

No dashboard feature may issue commands or change parameters.

---

### 11.5 Notifications
Telegram notifications must be supported as an output-only channel from Python.

Minimum notification types:
- Safety and lockout events (immediate)
- Flatten events (immediate)
- Communication loss / recovery
- Daily performance summary (scheduled)
- Optional heartbeat status (scheduled)

Notifications must be derived from stored logs/events and must never influence trading decisions.

---
### 11.3.1 Administrative Run Control (Optional, Admin Only)
The dashboard may provide an Admin-only control to toggle trading activity.

Rules:
- This control must only set a Python-side flag (e.g., `TRADING_ENABLED`).
- When disabled, Python must veto all new entries with reason_code manual_disabled.
- This control must not directly interact with NT8 or alter trade mechanics.
- Safety lockout and flatten actions always override this control.
- The control must not clear Safety lockouts.

Optional extension:
- A separate Admin-only “Flatten Now” action may exist, requiring explicit confirmation.

## 12. Status
Dashboard & Observability Design v1.0 — LOCKED
