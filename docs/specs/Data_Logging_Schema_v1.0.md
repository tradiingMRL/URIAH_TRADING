# URIAH_TRADING — Data Logging Schema v1.0

**Status:** ACTIVE  
**Scope:** Canonical logging schema for backtest + live (System A & B)  
**Linked Specs:** URIAH_TRADING_Core_v1.1.md, L2_Features_v1.0.md, LR_Features_SystemA_v1.0.md, LR_Features_SystemB_v1.0.md  
**Date:** 2026-02-02

---

## 1. Principles

- One canonical schema for System A and System B.
- Log at key lifecycle events: ENTRY_DECISION, ENTRY_FILL, EVAL, EXIT.
- Every decision must record:
  - outcome (DENY/PROCEED, HOLD/EXIT, etc.)
  - single reason code
  - minimal supporting metrics
- Version everything so old logs remain comparable even when specs evolve.

**Important policy:** Volatility is **observed and logged** in v1.0 but is **not a gating decision** yet.
Volatility gating will be introduced later as part of HMM v2 / second market-state gate.

---

## 2. Required Identifiers (present on every record)

- `ts_utc` (ISO 8601, UTC)
- `trade_id` (unique per attempt; persists across deny/entry/fill/eval/exit)
- `symbol`
- `system` (`A` or `B`)
- `event_type` (see Section 3)
- `direction` (`LONG` / `SHORT`)
- `session_id` (implementation-defined: e.g., date + session segment)
- `build_id` (git hash/tag of the running build)

Spec version fields:
- `spec_core_version` (e.g., `1.1`)
- `spec_l2_version` (e.g., `1.0`)
- `spec_lr_version` (e.g., `A1.0` or `B1.0`)
- `spec_logging_version` (`1.0`)

---

## 3. Event Types

### 3.1 `ENTRY_DECISION`
Logged whenever the system considers entry and either DENIES or PROCEEDS.

### 3.2 `ENTRY_FILL`
Logged when an entry order is filled (position established).

### 3.3 `EVAL`
Logged at post-entry evaluation triggers:
- `CVWAP_TOUCH`
- `CVWAP_CROSS`
- `STALL_CHECK`

### 3.4 `EXIT`
Logged when a position is closed.

---

## 4. Market Snapshot (minimal, required)

Required for ENTRY_DECISION, ENTRY_FILL, EVAL, EXIT:

Prices/micro:
- `last_price`
- `bid` (if available; else blank)
- `ask` (if available; else blank)
- `spread_ticks` (or proxy; if not available, log blank)

Volume/volatility observables (observational only in v1.0):
- `volume_rate` (per second; implementation-defined)
- `atr_short` (implementation-defined horizon)
- `atr_long`  (implementation-defined horizon)
- `range_ticks_recent` (range over recent window)
- `velocity_recent` (realized speed over recent window; units must be consistent)

Notes:
- These are logged to support future HMM v2 volatility-state work.
- Do not treat them as gates in v1.0.

---

## 5. Governance Snapshot (ENTRY_DECISION only)

### 5.1 Risk / Session Gates (implementation-defined)
- `risk_gate_pass` (0/1)
- `risk_gate_reason` (enum; blank if pass)

Recommended reason enums:
- `RISK_DAILY_DD_LOCKOUT`
- `RISK_CONSEC_LOSS_LOCKOUT`
- `RISK_MAX_TRADES_LOCKOUT`
- `RISK_SESSION_CLOSED`
- `RISK_SPREAD_TOO_WIDE` (only if you already have this as a deterministic safety rule)
- `RISK_OTHER`

### 5.2 Regime / Market State Gate (ENTRY ONLY)
- `regime_state` (`CHOP` / `BREAKOUT_WINDOW` / `LATE_TREND`)
- `regime_gate_pass` (0/1)
- `regime_gate_reason` (enum; blank if pass)

Recommended reason enums:
- `REGIME_BLOCKED_CHOP`
- `REGIME_BLOCKED_LATE_TREND`
- `REGIME_BLOCKED_OTHER`

### 5.3 Volatility State (observational only in v1.0)
These fields exist to train/validate future HMM v2 volatility regime.
- `vol_state_label` (optional; blank unless you choose to label it)
- `vol_notes` (optional free text; generally blank in automated logs)

---

## 6. Entry Decision Record (ENTRY_DECISION)

Required:
- `entry_decision` (`DENY` / `PROCEED`)
- `entry_reason_code` (single authoritative enum)

Examples (not exhaustive):
- `RISK_GATE_BLOCKED`
- `REGIME_GATE_BLOCKED`
- `SETUP_INVALID`
- `L2_NO_IMPACT`
- `LEVEL_NOT_HELD`
- `LR_ENTRY_VETO` (System B if you use LR at entry)
- `OTHER`

Also log:
- `setup_id` (implementation-defined: which setup pattern fired)
- `setup_quality_score` (optional numeric; blank if not used)

---

## 7. L2 Snapshot (ENTRY_DECISION + EVAL, system-dependent)

### 7.1 System A (from L2_Features_v1.0.md)
At breakout (ENTRY_DECISION if system=A):
- `A_L2_ImpactEfficiency_bucket` (`GOOD`/`POOR`)
- `A_L2_LevelPersistence_flag` (0/1)

At EVAL (system=A):
- log these again if you recompute them during management;
  otherwise leave blank.

### 7.2 System B (from L2_Features_v1.0.md)
At ENTRY_DECISION and EVAL (system=B):
- `B_L2_absorption_ratio_h1`
- `B_L2_absorption_ratio_h2`
- `B_L2_impact_eff_trend`
- `B_L2_liquidity_withdrawal_score`
- `B_L2_persistence_failure_count`

---

## 8. Order & Fill Record (ENTRY_FILL)

Required:
- `entry_order_type` (MARKET/LIMIT/STOP/other)
- `entry_order_price_requested` (blank if market)
- `entry_fill_price`
- `entry_sl_price`
- `entry_tp_price`
- `risk_R` (= |entry_fill_price - entry_sl_price|)
- `size_qty`

Execution diagnostics:
- `slippage_entry_ticks` (direction-aware; fill vs requested if applicable)
- `latency_ms` (optional; blank if not available)

---

## 9. Post-Entry Evaluation Record (EVAL)

### 9.1 Trigger metadata
- `eval_trigger` (`CVWAP_TOUCH` / `CVWAP_CROSS` / `STALL_CHECK`)
- `eval_elapsed_sec` (since entry)
- `eval_time_remaining_sec`

### 9.2 cVWAP (management-only control surface)
- `cVWAP`
- `cVWAP_offset_R`
- `cVWAP_slope`
- `cVWAP_cross_flag` (0/1)
- `cVWAP_dwell_ticks`

### 9.3 LR outputs (per system)
If system=A:
- `P_A`
- `LR_veto` (0/1)

If system=B:
- `P_B`
- `LR_veto` (0/1)

### 9.4 Time Feasibility (placeholders; values logged once implemented)
(Consistent with Core Spec v1.1; Kalman is management-only)
- `v_req`
- `v_k`
- `sigma_v`
- `v_cons`
- `L2_cap`
- `v_eff`
- `TIME_OK` (0/1)
- `time_veto_reason` (enum; blank if pass)

### 9.5 Management decision
- `mgmt_action` (`HOLD` / `EXIT`)
- `mgmt_reason_code` (single authoritative enum)

Recommended reason enums:
- `CATASTROPHIC_FAIL`
- `LR_VETO`
- `TIME_INFEASIBLE`
- `OTHER`

---

## 10. Exit Record (EXIT)

Required:
- `exit_type` (`TP` / `SL` / `TIMEOUT` / `MANUAL` / `OTHER`)
- `exit_reason_code` (single authoritative enum)
- `exit_order_price_requested` (blank if market)
- `exit_fill_price`

Execution diagnostics:
- `slippage_exit_ticks`

Performance:
- `pnl_ticks`
- `pnl_R`
- `mfe_R`
- `mae_R`
- `time_in_trade_sec`

---

## 11. Reason Code Policy (Important)

- Each decision uses **one** authoritative reason code:
  - entry deny reason
  - management action reason
  - exit reason
- Supporting metrics are logged separately (do not embed in reason text).

---

## 12. Change Control

- Any schema changes require bumping schema version: v1.1, v1.2, ...
- All logs must include:
  - `spec_*_version` fields
  - `build_id`
to preserve comparability across time and releases.

---

## 13. Deferred Work (Explicit)

Volatility gating is deferred to:
- HMM v2 / expanded market state
- second market-state gate (structural regime + volatility regime)

Until then, volatility is logged as observables only.