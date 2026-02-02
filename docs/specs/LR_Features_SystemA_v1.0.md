# URIAH_TRADING — Logistic Regression Feature Spec (System A) v1.0

**Status:** ACTIVE (Feature Definition Only)  
**Scope:** Logistic regression inputs for System A (Breakout)  
**Linked Core Spec:** URIAH_TRADING_Core_v1.1.md  
**Linked L2 Spec:** L2_Features_v1.0.md  
**Objective Label:** `Y_A = 1` if trade reaches TP before stop or timeout; else `0`  
**Version:** v1.0  
**Date:** 2026-02-02

---

## 1. Purpose & Guardrails

System A LR is used **post-entry only** as part of retracement/stall evaluation.
It is never used for entry triggers, regime gating, stops, targets, or sizing.

### Decision Context
LR is evaluated only at:
- cVWAP interaction (touch/cross/dwell), OR
- stall checkpoint

LR is the probability judge in the management stack:
1) catastrophic failure override (deterministic)
2) LR probability veto
3) time feasibility veto (authoritative)

---

## 2. Canonical Inputs (Units & Normalization)

All features must be normalized to reduce instrument dependence.

### Normalization Rules
- Price distances expressed in **R-units** (risk multiple) where possible:
  - `R = |entry_price - initial_stop|`
- Otherwise use **ticks**.
- Time expressed in **seconds** since entry or since event.

---

## 3. Feature Set v1.0 (Minimal, Robust)

### 3.1 State-of-Trade (post-entry context)
1. `A_elapsed_sec`  
   - seconds since entry
2. `A_time_remaining_frac`  
   - `(time_remaining_sec / max_trade_seconds)` clipped to `[0,1]`
3. `A_R_open`  
   - current open PnL in R: `(current_price - entry_price) * dir / R`
4. `A_R_mfe`  
   - max favorable excursion since entry in R
5. `A_R_mae`  
   - max adverse excursion since entry in R

### 3.2 Retracement Geometry (evaluated at cVWAP interaction or stall)
6. `A_pullback_from_peak_R`  
   - `(peak_price - current_price) * dir / R` where `peak_price` is post-entry peak in trade direction
7. `A_pullback_fraction`  
   - `A_pullback_from_peak_R / max(A_R_mfe, eps)` clipped `[0, 2]`
8. `A_retrace_speed_Rps`  
   - pullback distance in R divided by seconds since peak (R per second)
9. `A_distance_to_TP_R`  
   - remaining distance to target in R: `|tp_price - current_price| / R`

### 3.3 cVWAP Interaction (management-only control surface)
10. `A_cVWAP_offset_R`  
   - `(current_price - cVWAP) * dir / R`
11. `A_cVWAP_slope`  
   - slope of cVWAP over short horizon (unit: price/sec or R/sec)
12. `A_cVWAP_cross_flag`  
   - 1 if crossed cVWAP during the current evaluation window, else 0
13. `A_cVWAP_dwell_ticks`  
   - ticks spent inside the cVWAP band during evaluation window

### 3.4 Pressure / Momentum Proxies (price/volume only; no DOM dependence)
14. `A_impulse_efficiency`  
   - `A_R_mfe / max(elapsed_sec, 1)`  (R per sec)
15. `A_recent_volatility_R`  
   - short-horizon realized volatility in R (e.g., std of returns, scaled)
16. `A_volume_rate_z`  
   - z-score of volume rate vs recent baseline (instrument-specific baseline computed in data pipeline)

### 3.5 L2 Feature Inputs (supporting evidence only for System A)
System A LR may ingest only:
- `A_L2_ImpactEfficiency_bucket` (derived from L2 spec A1)
- `A_LevelPersistence_flag` (derived from L2 spec A2)

17. `A_L2_ImpactEfficiency_bucket`  
    - encoded as ordinal / one-hot (GOOD/POOR)
18. `A_L2_LevelPersistence_flag`  
    - 1 if persistence held, else 0

---

## 4. Explicit Exclusions (System A)

- No raw bid/offer imbalance features
- No queue position, order book slope, or cancellation metrics
- No Kalman pace features
- No regime state features post-entry (regime gating is entry-only)
- No stop/target-derived features that could create circularity beyond R normalization

---

## 5. Output & Thresholding

LR outputs:
- `P_A = P(reach TP before stop/timeout | current state)`

Operational use:
- Compared against `LR_TH_A` during management evaluation only.
- Threshold tuning is out-of-scope for this document.

---

## 6. Logging Requirements (per evaluation)

Log the full feature vector snapshot plus:
- `P_A`
- evaluation trigger type (`CVWAP_TOUCH` / `STALL_CHECK`)
- management decision and reason code