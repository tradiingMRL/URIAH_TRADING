# URIAH_TRADING — Logistic Regression Feature Spec (System B) v1.0

**Status:** ACTIVE (Feature Definition Only)  
**Scope:** Logistic regression inputs for System B (Mean Reversion)  
**Linked Core Spec:** URIAH_TRADING_Core_v1.1.md  
**Linked L2 Spec:** L2_Features_v1.0.md  
**Objective Label:** `Y_B = 1` if trade reaches reversion target (mean/TP) before stop or timeout; else `0`  
**Version:** v1.0  
**Date:** 2026-02-02

---

## 1. Purpose & Guardrails

System B LR is used:
- at entry (as part of turning-point validation, with L2-heavy evidence), and
- post-entry at retracement/stall checkpoints

It is never used for stops, targets, or sizing.
L2 is emphasized for System B by design.

---

## 2. Normalization

- Distances normalized in **R** when applicable.
- Also allowed: deviation-from-mean expressed in **sigma units** (e.g., SD bands) if those are part of System B’s defined setup.
- Time in seconds.

---

## 3. Feature Set v1.0 (Exhaustion-Focused, L2-Heavy)

### 3.1 Entry Context (turning-point candidate)
1. `B_elapsed_sec`  
   - seconds since entry (0 at entry evaluation)
2. `B_time_remaining_frac`  
   - `(time_remaining_sec / max_trade_seconds)` clipped `[0,1]`
3. `B_dev_from_mean_R`  
   - `(current_price - cVWAP) * dir_to_target / R` where `dir_to_target` is direction toward mean/TP
4. `B_dev_from_mean_sigma`  
   - deviation in sigma units if SD bands exist (else omit)
5. `B_distance_to_target_R`  
   - remaining distance to reversion target (mean/TP) in R

### 3.2 Reversion Dynamics (how the move is behaving)
6. `B_reversion_velocity_Rps`  
   - favorable movement toward target over short horizon / seconds
7. `B_adverse_pressure_Rps`  
   - movement away from target over short horizon / seconds
8. `B_chop_index`  
   - short-horizon directional efficiency (e.g., net move / total movement), scaled to [0,1]
9. `B_volatility_R`  
   - short-horizon realized volatility in R

### 3.3 cVWAP Interaction (management-only control surface)
10. `B_cVWAP_offset_R`  
    - `(current_price - cVWAP) * dir_to_target / R`
11. `B_cVWAP_slope`  
    - slope of cVWAP over short horizon
12. `B_cVWAP_cross_flag`  
    - 1 if crossed cVWAP during evaluation window, else 0
13. `B_cVWAP_dwell_ticks`  
    - ticks spent within cVWAP band

### 3.4 L2 Exhaustion Features (from L2_Features_v1.0.md; high weight)
System B LR may ingest:
- B1 Absorption ratio
- B2 Impact efficiency trend
- B3 Liquidity withdrawal near price
- B4 Persistence failure

14. `B_L2_absorption_ratio_h1`  
    - short horizon (e.g., 2–5 sec)
15. `B_L2_absorption_ratio_h2`  
    - medium short horizon (e.g., 10–30 sec)
16. `B_L2_impact_eff_trend`  
    - slope/delta over short window
17. `B_L2_liquidity_withdrawal_score`  
    - direction-aware near-price capacity decay score
18. `B_L2_persistence_failure_count`  
    - failed extension attempts per window

### 3.5 Price/Print Confirmation (non-DOM, anti-overfit)
19. `B_impact_per_volume_trend`  
    - print-based proxy aligned with L2 absorption (redundant check)
20. `B_volume_rate_z`  
    - volume rate z-score vs baseline
21. `B_spread_proxy`  
    - if true spread not available, use tick-to-tick price jitter proxy as microstructure stress

---

## 4. Explicit Exclusions (System B)

- No raw bid/offer imbalance as a primary feature
- No queue-position prediction
- No Kalman pace features for entry decisions (Kalman is locked to post-entry time feasibility only)
- No regime gating features beyond the entry gate itself

---

## 5. Output & Operational Use

LR outputs:
- `P_B = P(reach reversion target before stop/timeout | current state)`

Operational use:
- Entry permission requires:
  - structure/extreme condition is met, AND
  - L2 exhaustion evidence is present, AND
  - `P_B >= LR_TH_B`
- Post-entry, `P_B` is used during cVWAP interaction or stall checkpoints.

Threshold tuning is out-of-scope for this document.

---

## 6. Logging Requirements

At each LR evaluation event, log:
- all feature values
- `P_B`
- evaluation context (`ENTRY_EVAL`, `CVWAP_TOUCH`, `STALL_CHECK`)
- decision and reason code