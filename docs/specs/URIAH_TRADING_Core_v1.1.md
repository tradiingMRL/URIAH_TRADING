# URIAH_TRADING — Core Summary v1.1 (AUTHORITATIVE)

**Status:** ACTIVE CORE SPEC  
**Scope:** Trade lifecycle, regime governance, trade management, L2 usage, time feasibility  
**Version:** v1.1  
**Date:** 2026-02-02 (Australia/Melbourne)  
**Owner:** URIAH_TRADING

---

## CHANGELOG

### v1.1 (2026-02-02)
- Finalized regime naming: `CHOP`, `BREAKOUT_WINDOW`, `LATE_TREND`
- Clarified governance: regime gating applies **ENTRY ONLY**; post-entry uses premise validity kitbag
- Introduced management-only control surface: `cVWAP = mean(eVWAP, PW-VWAP)` (explicitly forbidden for entry/regime/stops/sizing)
- Defined retracement evaluation stack: catastrophic failure → LR probability → time feasibility veto
- Formalized time feasibility using Kalman pace + uncertainty + L2 capacity factor
- Locked Kalman usage to post-entry time feasibility only (computed at entry, updated on ticks)
- Added L2 usage policy (System A light / System B heavy) and initial L2 feature specs
- Added NON-OPERATIONAL “Future Enhancements” + explicit reminder note about Kalman-at-entry research only

---

## 1. Core Philosophy (Non-Negotiables)

- Risk-first, governance-driven system
- Fail-safe default = **NO TRADE**
- One position at a time (account-level mutex)
- **Regime gating applies only at entry** (permission to open trades)
- Active trades are managed by **premise validity**, not regime flips
- All decisions are logged with reason codes

---

## 2. Regime States (FINAL)

CHOP
BREAKOUT_WINDOW
LATE_TREND

### System A (Breakout)
- Allowed **only** in `BREAKOUT_WINDOW`
- Disabled once trend becomes **mature** (`LATE_TREND`)
- Early continuation is valid; late continuation is not

### System B (Mean Reversion)
- Trades against extended movement
- Requires explicit **exhaustion confirmation** (L2-heavy)

---

## 3. Trade Lifecycle (High Level)

1. Session / Risk gates  
2. Regime gate (ENTRY ONLY)  
3. Setup qualification  
4. Entry trigger  
5. Position construction  
6. Execution  
7. Post-entry management (core intelligence)  
8. Exit  
9. Logging & feedback  

---

## 4. Post-Entry Trade Management (Core Intelligence)

### 4.1 Control Surface (Management-Only)
- **cVWAP = mean(eVWAP, PW-VWAP)**
- Used **only post-entry**
- Explicitly forbidden for:
  - regime gating
  - entry triggers
  - stop placement (initial or trailing)
  - sizing
  - anything that increases risk

---

### 4.2 Retracement Evaluation (Unified Pattern for A & B)

Retracement/stall evaluation is triggered **only** when:
- price interacts with cVWAP (touch/cross/dwell), OR
- a stall checkpoint triggers review

Decision stack priority order:

1. **Catastrophic premise failure** (deterministic)
2. **Logistic regression probability**
3. **Time feasibility veto** (authoritative veto)

---

## 5. Time Feasibility (AUTHORITATIVE)

Time feasibility asks:

> Is it still realistically possible to reach TP in the remaining time?

### Inputs
- Distance remaining to TP
- Time remaining (trade duration budget)
- Kalman-estimated forward pace: `v_k`
- Kalman uncertainty: `σ_v`
- L2 liquidity capacity factor: `cap`

### Rule (Locked)

v_eff = max(v_k − k_unc·σ_v, v_floor) × cap
TIME_OK = (required_velocity ≤ v_eff × margin)

- Exit reason remains: `TIME_INFEASIBLE`
- Kalman and L2 **never** cause exits directly; they only inform feasibility

---

## 6. Kalman Filter Lockout Policy (FINAL)

### Allowed
- Kalman pace + uncertainty is initialized at entry (baseline)
- Updated on ticks while trade is live
- Used **only** for post-entry time feasibility

### Forbidden
Kalman outputs must never be referenced by:
- regime gating / state classification
- setup qualification
- entry triggers
- stop/target placement
- position sizing
- any alpha generation or “permission to add”

**Principle:** Kalman may only reduce false hope, never create opportunity.

---

## 7. Level-2 (L2) Usage Policy (FINAL)

### Global Rules
- No tick prediction
- No DOM-based stops or targets
- No reliance on raw bid/offer imbalance as primary signal
- L2 is contextual evidence only (feeds LR and capacity; never standalone entry/exit)

---

### System A — Breakout (Light L2 Use)
**When**
1. At breakout (entry quality check)
2. During retracement evaluation (supporting evidence only)

**Authority**
- Binary quality filter at entry
- Post-entry: evidence only (never standalone exit)

---

### System B — Mean Reversion (Heavy L2 Use)
**When**
1. At entry (turning-point / exhaustion validation)
2. During retracement/stall reviews (high weight)

**Authority**
- Primary exhaustion confirmation at entry
- Heavy weighting inside LR
- Influences time feasibility via capacity factor

---

## 8. Logging (Minimum Required)

At each evaluation event, log at minimum:
- regime at entry
- setup type
- cVWAP interaction flags
- LR probability (if available)
- time feasibility metrics: `v_req`, `v_k`, `σ_v`, `v_cons`, `cap`, `v_eff`, `TIME_OK`
- L2 capacity state / score
- exit reason code

---

## 9. L2 Feature Specs v1.0

### System A — Minimal, Final (only A1 & A2)

#### A1. Impact Efficiency (Primary)
Purpose: distinguish real initiative from “air breaks”.

Definition:

ImpactEfficiency = |ΔPrice| / AggressiveVolume

Window: breakout bar / breakout tick cluster  
Output: `GOOD` / `POOR`

#### A2. Level Persistence (Secondary)
Purpose: ensure breakout level holds.

Definition:
- after breakout, price must remain outside prior balance for N ticks or ms
- immediate re-entry = failure

Output: `GOOD` / `POOR`

**Entry Rule**
- If A1 POOR → deny entry (`L2_NO_IMPACT`)
- Else if A2 POOR → deny entry (`LEVEL_NOT_HELD`)
- Else allow entry

---

### System B — Exhaustion-Focused (L2-heavy)

#### B1. Impact vs Absorption Ratio
Aggressive volume vs resulting price change.
Low impact = exhaustion evidence.

#### B2. Impact Efficiency Trend
Is impact efficiency degrading over short horizon?

#### B3. Liquidity Withdrawal Near Price
Direction-aware thinning of supportive liquidity near price.
Used as capacity evidence (not imbalance signal).

#### B4. Persistence Failure
Repeated attempts to extend fail despite aggression.

**Usage**
- feeds LR feature vector (high weight)
- contributes to L2 capacity factor used in time feasibility
- re-evaluated at stall checkpoints

---

## 10. Future Enhancements (NON-OPERATIONAL)

> Items here are explicitly NOT part of the live system.  
> No item may be implemented without formal promotion + data validation (walk-forward).

### System A — Possible
- Entry-time feasibility filter: compare entry feasibility estimate to distribution of winning trades; deny if worse than ~1 SD from winners
- refined breakout quality metrics (still minimal / coarse)
- adaptive breakout window duration (must not violate risk envelope)

### System B — Possible
- deeper microstructure exhaustion classifiers (must feed LR only)

---

## 11. Explicit Reminder (Locked Note)

Kalman pace + uncertainty may be evaluated at entry for research purposes only in the future.
It is currently restricted to post-entry time feasibility and must not influence live entry decisions.





