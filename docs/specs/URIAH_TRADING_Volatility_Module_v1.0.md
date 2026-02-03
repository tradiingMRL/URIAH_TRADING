# URIAH_TRADING — Volatility Module v1.0 (LOCKED)

## 1. Purpose
The Volatility Module classifies the **execution environment** so that:
- Unreliable environments are blocked
- Reliable environments are traded by the appropriate system
- Early exit logic is not polluted by noise or transient spikes

Volatility here represents **execution and structural trustworthiness**, not price direction or range.

This module is **permissioning only**.  
It never places trades, exits trades, or modifies trade mechanics.

---

## 2. Inputs

### 2.1 Price-Based (Time-Normalised)
Computed on a fixed time grid (e.g. 1s / 5s / 15s):

- `v_abs`  
  Absolute price velocity (|Δprice| / Δt)

- `v_var`  
  Variance of raw velocity over rolling window

- `v_impulse`  
  Impulse density  
  Σ|Δprice| over window / window duration

### 2.2 Participation-Based (L2)
Derived from order book / tape behaviour:

- `L2_stress ∈ [0, 1]`  
  Composite of:
  - Liquidity pull rate
  - Absolute consumption intensity
  - Refill stability

L2_stress is:
- Non-directional
- Bounded
- Normalised vs recent baseline

---

## 3. Derived Volatility Measures

### 3.1 Volatility Intensity
A monotonic composite scalar:

VI(t) = f(v_abs, v_var, v_impulse, L2_stress)

Higher VI = more hostile execution environment.

No thresholds or decisions are applied at this level.

---

### 3.2 Smoothed Volatility
Two EMAs are maintained:

VI_fast(t) = EMA(VI, α_fast)
VI_slow(t) = EMA(VI, α_slow)

- `VI_fast` reacts to emergent danger
- `VI_slow` represents background regime

---

### 3.3 Volatility Slope (Regime Trend)
Defined as:

VI_slope(t) = VI_fast(t) − VI_slow(t)

Interpretation:
- `VI_slope > 0` → volatility escalating
- `VI_slope ≈ 0` → volatility stable
- `VI_slope < 0` → volatility decaying

This slope is **not directional**.  
It measures the *trend of volatility itself*.

---

## 4. Volatility States (Final)

### 4.1 HOT
**Definition**
- Velocity high and/or unstable
- Participation stressed
- Volatility escalating or sustained

Formal conditions:
- Instantaneous HOT criteria met
- `VI_slope ≥ 0`
- Minimum confirmation dwell satisfied

**Interpretation**
Fast + fragile → unreliable execution

**System Behaviour**
- ❌ System A: BLOCK
- ❌ System B: BLOCK
- ❌ All new entries blocked
- ⚠️ May trigger Exit Review (policy-dependent)

---

### 4.2 NORMAL
**Definition**
- Velocity within bounds
- Participation healthy
- Volatility stable

Formal conditions:
- Not HOT
- Not INERT
- `VI_slope ≈ 0`
- Minimum confirmation dwell satisfied

**Interpretation**
Reliable, tradable environment

**System Behaviour**
- ✅ System A: ALLOW
- ✅ System B: ALLOW

---

### 4.3 INERT (formerly “DEAD”)
**Definition**
- Velocity low
- Impulse sparse
- Participation calm or disengaged
- Volatility decaying or flat

Formal conditions:
- Low `v_abs` and `v_impulse`
- `VI_slope ≤ 0`
- Minimum confirmation dwell satisfied

**Interpretation**
Energy absent, not chaotic  
Breakouts unlikely, mean reversion may be viable

**System Behaviour**
- ❌ System A: BLOCK
- ⚠️ System B: CONDITIONAL

System B may trade INERT **only if**:
- Price is meaningfully displaced from EVWAP/value
- A defined mean-reversion zone exists
- L2 shows absorption / passive defence
- Velocity is low but non-zero

---

## 5. Anti-Spike and Anti-Thrash Rules

- State transitions require:
  - Instantaneous condition
  - Volatility slope alignment
  - Minimum dwell time
- Single or short-lived spikes cannot flip state
- Priority ordering:
  - HOT overrides all
  - INERT overrides NORMAL

---

## 6. System Integration Rules

### 6.1 Entry Permission
- Entries only allowed when volatility state permits
- Volatility does not select strategy or direction

### 6.2 Early Exit Engine
- Volatility never modifies trade mechanics
- Volatility may trigger an Exit Review
- Volatility always provides context to Exit Review

### 6.3 HMM
- HMM runs in all volatility states
- HMM confidence may be down-weighted in HOT or INERT
- HMM never overrides volatility

### 6.4 Safety
Safety overrides volatility under all circumstances.

---

## 7. Logging (Mandatory)

File: `volatility_log.csv`

Fields:
- `ts`
- `vol_state`
- `VI_fast`
- `VI_slow`
- `VI_slope`
- `v_abs`
- `v_var`
- `v_impulse`
- `L2_stress`
- `state_dwell_sec`
- `reason_code`

Volatility decisions must always be explainable via logs.

---

## 8. Invariants (Non-Negotiable)

- Volatility module never places trades
- Volatility module never exits trades
- Volatility module never tunes parameters
- Volatility must be resolved before Early Exit logic
- Volatility states are stable, auditable, and explainable

---

## 9. Mental Model (Authoritative)

- HOT → protect capital
- NORMAL → trade as designed
- INERT → fade carefully, only if there is something to fade

---

## 10. Status

**Volatility Module v1.0 — LOCKED**

This module is complete and ready for implementation.
Changes require empirical evidence, not intuition.


