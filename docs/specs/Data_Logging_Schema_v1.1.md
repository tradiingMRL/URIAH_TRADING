# URIAH_TRADING — Data Logging Schema v1.1

**Status:** ACTIVE  
**Scope:** Canonical logging schema for backtest + live (System A & B)  
**Linked Specs:** URIAH_TRADING_Core_v1.1.md, L2_Features_v1.0.md, LR_Features_SystemA_v1.0.md, LR_Features_SystemB_v1.0.md  
**Date:** 2026-02-02

---

## 1. Principles

- One canonical schema for System A and System B.
- Log at key lifecycle events:
  - ENTRY_DECISION (includes DENY = rejected opportunities)
  - ENTRY_FILL
  - EVAL (single-shot checkpoints; no tick spam)
  - EXIT (accounting truth)
  - LOCKOUT_EVENT (governance state change)
- Every decision must record:
  - outcome (DENY/PROCEED, HOLD/EXIT, etc.)
  - single reason code
  - minimal supporting metrics as separate numeric fields
- Version everything so old logs remain comparable as specs evolve.

**Important policy:** Volatility is **observed and logged** in v1.1 but is **not a gating decision** yet.
Volatility gating will be introduced later as part of HMM v2 / second market-state gate.

**Fee policy:** Only log fees that occur *because a trade was taken* (commission, exchange/clearing, regulatory, per-order/contract fees).
Do not log platform/data/VPS overhead here.

---

## 2. Required Identifiers (present on every record)

- `ts_utc` (ISO 8601, UTC)
- `trade_id` (unique per attempt; persists across deny/entry/fill/eval/exit)
- `symbol`
- `system` (`A` or `B`)
- `event_type` (see Section 3)
- `direction` (`LONG` / `SHORT` or blank if not applicable)
- `session_id` (implementation-defined: e.g., date + session segment)
- `build_id` (git hash/tag of the running build)

Spec version fields:
- `spec_core_version` (e.g., `1.1`)
- `spec_l2_version` (e.g., `1.0`)
- `spec_lr_version` (e.g., `A1.0` or `B1.0`)
- `spec_logging_version` (`1.1`)

---

## 3. Event Types

### 3.1 `ENTRY_DECISION`
Logged whenever the system considers entry and either DENIES or PROCEEDS.
**DENY rows are mandatory** (these are your rejected opportunities dataset).

### 3.2 `ENTRY_FILL`
Logged when an entry order is filled (position established).

### 3.3 `EVAL`
Logged at post-entry evaluation triggers (single-shot, not per-tick):
- `CVWAP_TOUCH`
- `CVWAP_CROSS`
- `STALL_CHECK`
- `A_BOX_REENTRY` (System A only; first time price re-enters box after entry)

### 3.4 `EXIT`
Logged when a position is closed (accounting truth).

### 3.5 `LOCKOUT_EVENT`
Logged only when lockout state changes ON/OFF (governance audit trail).

---

## 4. Time & Session Fields (required where available)

Required on all rows when exchange-local time is known; otherwise leave blank:
- `ts_exchange` (ISO timestamp in exchange timezone)
- `tod_minute` (0–1439 in exchange timezone)
- `tod_bucket` (implementation-defined label; used for time-of-day studies)
- `dow` (1–7)
- `session_type` (`RTH`/`ETH`)

---

## 5. Account & Governance Snapshot (required where available)

Log on all rows if the platform supports it; at minimum on ENTRY_DECISION and EXIT:

- `account_equity` (required where available; equity curve)
- `account_balance` (optional if not available)
- `account_unrealized_pnl` (optional)

Drawdown/HWM (day/session; optional until implemented):
- `equity_hwm_day`
- `equity_dd_from_hwm_day`
- `equity_dd_from_hwm_day_pct`

Risk counters (at minimum on ENTRY_DECISION and EXIT):
- `trades_taken_today`
- `trades_denied_today`
- `net_pnl_today` (optional snapshot; net of trade-attributable fees)
- `consec_losses`
- `lockout_active` (0/1)
- `lockout_reason` (enum; blank if none)

Note: `consec_wins` is intentionally NOT tracked.

---

## 6. Market Snapshot (minimal, required)

Required for ENTRY_DECISION, ENTRY_FILL, EVAL, EXIT:

Prices/micro:
- `last_price`
- `bid` (if available; else blank)
- `ask` (if available; else blank)
- `spread_ticks` (or proxy; if not available, log blank)

Volume/volatility observables (observational only in v1.1):
- `volume_rate` (per second; implementation-defined)
- `atr_short` (implementation-defined horizon)
- `atr_long`  (implementation-defined horizon)
- `range_ticks_recent` (range over recent window)
- `velocity_recent` (realized speed over recent window; units must be consistent)

---

## 7. Governance Snapshot (ENTRY_DECISION only)

### 7.1 Risk / Session Gates (implementation-defined)
- `risk_gate_pass` (0/1)
- `risk_gate_reason` (enum; blank if pass)

Recommended reason enums:
- `RISK_DAILY_DD_LOCKOUT`
- `RISK_CONSEC_LOSS_LOCKOUT`
- `RISK_MAX_TRADES_LOCKOUT`
- `RISK_SESSION_CLOSED`
- `RISK_SPREAD_TOO_WIDE` (only if deterministic safety rule)
- `RISK_OTHER`

### 7.2 Regime / Market State Gate (ENTRY ONLY)
- `regime_state` (`CHOP` / `BREAKOUT_WINDOW` / `LATE_TREND`)
- `regime_gate_pass` (0/1)
- `regime_gate_reason` (enum; blank if pass)

Recommended reason enums:
- `REGIME_BLOCKED_CHOP`
- `REGIME_BLOCKED_LATE_TREND`
- `REGIME_BLOCKED_OTHER`

### 7.3 Volatility State (observational only in v1.1)
For future HMM v2 volatility regime work:
- `vol_state_label` (optional; blank unless you label)
- `vol_notes` (optional; generally blank)

---

## 8. Entry Decision Record (ENTRY_DECISION)

Required:
- `entry_decision` (`DENY` / `PROCEED`)
- `entry_reason_code` (single authoritative enum)

Examples (not exhaustive):
- `RISK_GATE_BLOCKED`
- `REGIME_GATE_BLOCKED`
- `SETUP_INVALID`
- `L2_NO_IMPACT`
- `LEVEL_NOT_HELD`
- `LR_ENTRY_VETO` (if LR used at entry)
- `OTHER`

Also log:
- `setup_id` (implementation-defined: which setup pattern fired)
- `setup_quality_score` (optional numeric; blank if not used)

---

## 9. L2 Snapshot (ENTRY_DECISION + EVAL, system-dependent)

### 9.1 System A (from L2_Features_v1.0.md)
At breakout (ENTRY_DECISION if system=A):
- `A_L2_ImpactEfficiency_bucket` (`GOOD`/`POOR`)
- `A_L2_LevelPersistence_flag` (0/1)

At EVAL (system=A):
- log these again if recomputed during management; otherwise leave blank.

### 9.2 System B (from L2_Features_v1.0.md)
At ENTRY_DECISION and EVAL (system=B):
- `B_L2_absorption_ratio_h1`
- `B_L2_absorption_ratio_h2`
- `B_L2_impact_eff_trend`
- `B_L2_liquidity_withdrawal_score`
- `B_L2_persistence_failure_count`

---

## 10. System A Box Snapshot (ENTRY_DECISION and/or ENTRY_FILL when available)

If system=A, log when box exists:
- `A_box_id` (optional)
- `A_box_high`
- `A_box_low`
- `A_box_height_ticks`
- `A_box_age_bars`
- `A_box_touches`
- `A_breakout_side` (`UP`/`DOWN`)
- `A_box_boundary_price` (top for LONG, bottom for SHORT)

Distance-from-box gate (≤ 0.5×ATR; if used):
- `A_atr_ref`
- `A_entry_ref_price`
- `A_dist_from_box_ticks`
- `A_dist_from_box_atr`
- `A_gate_dist_from_box_pass` (0/1)
- `A_gate_dist_from_box_thresh_atr` (fixed: 0.5)

---

## 11. Order & Fill Record (ENTRY_FILL)

Required:
- `entry_order_type` (MARKET/LIMIT/STOP/other)
- `entry_order_price_requested` (blank if market)
- `entry_fill_price`
- `entry_sl_price`
- `entry_tp_price`
- `risk_price_ticks` (= |entry_fill_price - entry_sl_price| in ticks)
- `risk_$` (dollar risk at entry)
- `size_qty`

Margin (required where available):
- `margin_initial`
- `margin_maintenance` (optional)
- `margin_currency`
- `margin_to_equity_frac` (= margin_initial / account_equity; optional if equity unavailable)

Execution diagnostics:
- `slippage_entry_ticks` (direction-aware; fill vs requested if applicable)
- `latency_ms` (optional; blank if not available)

---

## 12. Post-Entry Evaluation Record (EVAL)

### 12.1 Trigger metadata
- `eval_trigger` (`CVWAP_TOUCH` / `CVWAP_CROSS` / `STALL_CHECK` / `A_BOX_REENTRY`)
- `eval_elapsed_sec` (since entry)
- `eval_time_remaining_sec`

### 12.2 cVWAP (management-only control surface)
- `cVWAP`
- `cVWAP_offset_R`
- `cVWAP_slope`
- `cVWAP_cross_flag` (0/1)
- `cVWAP_dwell_ticks`

### 12.3 LR outputs (per system)
If system=A:
- `P_A`
- `LR_veto` (0/1)

If system=B:
- `P_B`
- `LR_veto` (0/1)

### 12.4 Time Feasibility (placeholders; values logged once implemented)
(Consistent with Core Spec v1.1; Kalman is management-only)
- `v_req`
- `v_k`
- `sigma_v`
- `v_cons`
- `L2_cap`
- `v_eff`
- `TIME_OK` (0/1)
- `time_veto_reason` (enum; blank if pass)

### 12.5 Management decision
- `mgmt_action` (`HOLD` / `EXIT`)
- `mgmt_reason_code` (single authoritative enum)

Recommended reason enums:
- `CATASTROPHIC_FAIL`
- `LR_VETO`
- `TIME_INFEASIBLE`
- `A_BOX_REENTRY` (if action is EXIT due to re-entry logic)
- `OTHER`

### 12.6 System A “box re-entry” fields (only when eval_trigger = A_BOX_REENTRY)
- `A_box_reentry_flag` (0/1)
- `A_box_reentry_price`
- `A_box_reentry_elapsed_sec`
- `A_box_reentry_depth_ticks`

---

## 13. Exit Record (EXIT) — Accounting Truth

Required:
- `exit_type` (`TP` / `SL` / `TIMEOUT` / `EARLY_EXIT` / `MANUAL` / `OTHER`)
- `exit_reason_code` (single authoritative enum)
- `exit_order_price_requested` (blank if market)
- `exit_fill_price`

Execution diagnostics:
- `slippage_exit_ticks`

Accounting (gross vs net):
- `pnl_gross`
- `fees_trade_total`
- `pnl_net`

Risk-adjusted:
- `risk_$`
- `R_gross` (= pnl_gross / risk_$)
- `R_net` (= pnl_net / risk_$)

Time-efficiency:
- `time_in_trade_sec`
- `net_per_min` (= pnl_net / (time_in_trade_sec / 60))

Excursions:
- `mfe_R`
- `mae_R`
(Optional later: mfe_ticks/mae_ticks if you want)

System A early-exit (“fell back into the box and stayed there”):
- `exit_reason_code = A_BOX_REENTRY_STALL`
- `A_box_reentry_dwell_sec` (time inside box before exit)
- `A_box_reentry_max_depth_ticks`
- `A_box_reentry_exit_flag` (0/1)

---

## 14. Lockout Events (LOCKOUT_EVENT)

Logged only when lockout state changes:
- `lockout_state` (`ON` / `OFF`)
- `lockout_reason` (enum)
- `lockout_scope` (`SYSTEM` / `SYSTEM_A` / `SYSTEM_B`)

Optional numeric context (only if available):
- `lockout_threshold_value`
- `lockout_trigger_value`

Suggested reasons (extend as needed):
- `LOCKOUT_DAILY_DD`
- `LOCKOUT_CONSEC_LOSSES`
- `LOCKOUT_MAX_TRADES`
- `LOCKOUT_SESSION_END`
- `LOCKOUT_MANUAL`
- `LOCKOUT_MODULE_FAILURE`
- `LOCKOUT_NETWORK_DEGRADED` (reserved)

---

## 15. Reason Code Policy (Important)

- Each decision uses one authoritative reason code:
  - entry deny reason
  - management action reason
  - exit reason
  - lockout reason
- Supporting metrics are logged in separate fields (do not embed in reason text).

---

## 16. Change Control

- Any schema changes require bumping schema version: v1.2, v1.3, ...
- All logs must include:
  - `spec_*_version` fields
  - `build_id`
to preserve comparability across time and releases.

---

## 17. Deferred Work (Explicit)

Volatility gating is deferred to:
- HMM v2 / expanded market state
- second market-state gate (structural regime + volatility regime)

Until then, volatility is logged as observables only.