# URIAH_TRADING — Level-2 Feature Specifications v1.0

**Status:** ACTIVE (Feature Definition Only)  
**Scope:** Level-2 features for System A (Breakout) and System B (Mean Reversion)  
**Linked Core Spec:** URIAH_TRADING_Core_v1.1.md  
**Version:** v1.0  
**Date:** 2026-02-02

---

## 1. Purpose & Guardrails

This document defines the **exact Level-2 (L2) feature set** used by URIAH_TRADING.

### Non-Negotiables
- L2 is **never** used for tick prediction
- L2 is **never** used for stop placement, target placement, or sizing
- L2 is **never** a standalone entry or exit trigger
- Raw bid/offer imbalance is explicitly excluded as a primary signal

L2 features serve **contextual evidence roles only**, feeding:
- entry quality checks (System A)
- exhaustion validation (System B)
- logistic regression features
- time-feasibility capacity adjustment

---

## 2. Shared Definitions

### Aggressive Volume
- Volume executed **at the ask** (buys) or **at the bid** (sells)
- Trade direction inferred via standard classification (e.g. tick rule / quote rule)

### Impact Window
- A short, fixed horizon aligned to the decision point:
  - breakout bar / breakout tick cluster (System A)
  - exhaustion or stall checkpoint (System B)

---

## 3. System A — Breakout (Minimal, Binary L2 Use)

System A uses **only two L2 features**.
No others are permitted.

### Authority Level
- **Binary quality filter**
- Evaluated at breakout
- Supporting evidence only during post-entry retracement review

---

### A1. Impact Efficiency (Primary)

**Purpose**  
Distinguish real initiative from “air breaks”.

**Concept**  
If aggressive volume occurs but price barely moves, the breakout lacks quality.

**Definition**

ImpactEfficiency = |ΔPrice| / AggressiveVolume

- ΔPrice measured over breakout impact window
- Direction-aware (long vs short)

**Evaluation**
- Bucketed internally to avoid overfitting
- Output:
  - `GOOD`
  - `POOR`

**Usage**
- If `POOR` → entry is denied
- Logged as: `L2_IMPACT_EFF=GOOD|POOR`

---

### A2. Level Persistence (Secondary)

**Purpose**  
Confirm the breakout level is not immediately rejected.

**Concept**  
A valid breakout must **stay broken**.

**Definition**
- After breakout, price must remain outside prior balance / box
- Observation window:
  - N ticks or
  - M milliseconds

**Failure Condition**
- Immediate re-entry into the broken range

**Output**
- `GOOD`
- `POOR`

**Usage**
- If `POOR` → entry is denied
- Logged as: `L2_LEVEL_PERSIST=GOOD|POOR`

---

### System A Entry Rule (Final)

IF ImpactEfficiency == POOR → DENY ENTRY (L2_NO_IMPACT)
ELSE IF LevelPersistence == POOR → DENY ENTRY (LEVEL_NOT_HELD)
ELSE → ALLOW ENTRY

No weighting.  
No probability.  
No tuning.

---

## 4. System B — Mean Reversion (Exhaustion-Focused, L2-Heavy)

System B uses L2 as a **primary confirmation layer**.

### Authority Level
- Required for entry
- High-weight inputs to logistic regression
- Capacity evidence for time feasibility
- Re-evaluated during stall/retracement reviews

---

### B1. Impact vs Absorption Ratio

**Purpose**  
Detect exhaustion via ineffective aggression.

**Concept**  
Aggressive flow without proportional price movement indicates absorption.

**Definition**

AbsorptionRatio = |ΔPrice| / AggressiveVolume

- Same structure as System A, but:
  - evaluated across multiple short horizons
  - interpreted probabilistically, not binary

**Interpretation**
- Lower values → stronger exhaustion evidence

---

### B2. Impact Efficiency Trend

**Purpose**  
Detect deterioration in pressure quality.

**Concept**  
Exhaustion is often visible as **declining impact efficiency over time**.

**Definition**
- Track ImpactEfficiency over rolling short windows
- Compute slope / delta of efficiency

**Interpretation**
- Negative trend → exhaustion strengthening
- Positive trend → pressure re-asserting

---

### B3. Liquidity Withdrawal Near Price

**Purpose**  
Estimate **capacity** to continue the current directional move.

**Concept**  
When supportive liquidity thins near price, continuation becomes less feasible.

**Definition**
- Direction-aware measurement of near-price liquidity change
- Focus on **change**, not absolute depth
- No raw bid/offer imbalance

**Output**
- Continuous score used to compute `L2_CAPACITY`

---

### B4. Persistence Failure

**Purpose**  
Detect repeated failure to extend despite aggression.

**Concept**  
Multiple failed extension attempts signal control loss.

**Definition**
- Count failed extension attempts within short horizon
- Evaluate against aggression intensity

**Interpretation**
- High failure rate → exhaustion confirmation

---

## 5. L2 Capacity Factor (Shared Concept)

### Purpose
Adjust **time feasibility** realism.

### Definition

L2_CAPACITY ∈ [CAP_MIN … CAP_MAX]

Typical interpretation:
- `< 1.0` → capacity deteriorating
- `≈ 1.0` → neutral
- `> 1.0` → supportive (rare, early impulse only)

### Usage
- Multiplies Kalman-derived conservative pace
- Never used standalone
- Never causes exits directly

---

## 6. Integration Summary

| System | Entry Use | Post-Entry Use | Authority |
|------|----------|---------------|----------|
| A | Binary quality filter | Supporting evidence | Light |
| B | Mandatory exhaustion validation | High-weight evidence | Heavy |

---

## 7. Logging (Minimum)

At each L2 evaluation point, log:
- Feature values
- Bucketed outputs
- Capacity factor
- Decision context (entry / retracement / stall)

---

## 8. Explicit Exclusions

The following are **explicitly out of scope**:
- Raw bid/offer imbalance models
- Queue position prediction
- DOM-based forecasting
- Tick-level price prediction

---

## 9. Change Control

Any change to this document requires:
- Core spec compatibility check
- Version increment (v1.1, v1.2, …)
- Explicit commit message referencing reason for change



