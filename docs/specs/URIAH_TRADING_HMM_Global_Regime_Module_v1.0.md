# URIAH_TRADING — HMM Global Regime Module v1.0 (LOCKED)

## 1. Purpose
The HMM Global Regime Module classifies the **market regime** so that:
- Trades are only entered when the regime supports the strategy
- Trades may be exited early when the regime invalidates the thesis
- Strategy logic never reacts blindly to local price noise

The HMM is a **global gate and context provider**.
It never places trades and never manages trade mechanics.

---

## 2. Authority and Boundaries (Non-Negotiable)

The HMM module:

- ❌ Never generates trade signals
- ❌ Never selects direction
- ❌ Never modifies stops, targets, or sizing
- ❌ Never overrides Safety or Volatility

The HMM module **may**:
- Veto entries
- Trigger Exit Reviews
- Provide regime context to Early Exit logic

Priority order is fixed:
Safety > Volatility > HMM > Strategy

---

## 3. Inputs

### 3.1 Market Structure Inputs (Time-Normalised)
Computed on a fixed sampling grid:

- Directional efficiency (net movement / total movement)
- Directional persistence (short-lag autocorrelation)
- Range position stability
- EVWAP displacement behaviour (non-price-based)
- Velocity decay (from Volatility module)
- Participation stability (volume / trade count, non-directional)

### 3.2 Explicit Exclusions
The HMM **does not** consume:
- Stops or targets
- Trade PnL
- Entry signals
- Order outcomes

---

## 4. Hidden States (Final)

The HMM operates with **four and only four** states.

### 4.1 TREND
- Directional persistence
- Efficient movement
- EVWAP displacement sustained
- Continuation likely

### 4.2 MEAN_REVERT
- Oscillation around value
- Low directional efficiency
- Frequent EVWAP interaction

### 4.3 CHAOTIC
- High churn
- Poor persistence
- Conflicting signals
- Structural instability

### 4.4 DEAD
- Structural stagnation
- Low informational content
- Weak participation
- No reliable regime

---

## 5. Inference Mechanics

### 5.1 Posterior Estimation
At each HMM update:
- Full posterior distribution is maintained
- Output includes:
  - `state`
  - `confidence = max(posterior)`
  - `margin = max(posterior) − second_max(posterior)`

### 5.2 Anti-Thrash Discipline
State transitions require:
- Confidence ≥ `CONF_MIN`
- Margin ≥ `MARGIN_MIN`
- Minimum dwell time satisfied
- K consecutive confirmations

Single-bar regime flips are forbidden.

---

## 6. Strategy Compatibility Matrix (LOCKED)

| HMM State | System A (Breakout) | System B (Mean Reversion) |
|---------|--------------------|---------------------------|
| TREND | ✅ Allowed | ⚠️ Conditional |
| MEAN_REVERT | ❌ Blocked | ✅ Allowed |
| CHAOTIC | ❌ Blocked | ❌ Blocked |
| DEAD | ❌ Blocked | ❌ Blocked |

HMM **never chooses** the strategy.
It only vetoes incompatibilities.

---

## 7. Entry Gating Rules

Before any entry may proceed:
- Volatility must allow
- HMM must allow

### Entry Veto Conditions
- CHAOTIC or DEAD → veto all entries
- MEAN_REVERT → veto System A
- TREND → System B allowed only with structure confirmation

All vetoes are logged.

---

## 8. Exit Review Triggers

The HMM **never exits trades directly**.

It may trigger an Exit Review when:
- A confirmed state transition occurs
- The new state is hostile to the open strategy

The Exit Review engine then decides:
- `PERSIST`
- `EXIT_EARLY`

---

## 9. Interaction with Volatility

- HMM runs continuously in all volatility states
- HMM confidence may be down-weighted in HOT or INERT
- Volatility always has veto priority
- HMM never overrides volatility state

---

## 10. Logging (Mandatory)

### hmm_state_log.csv
- `ts`
- `state`
- `confidence`
- `margin`
- `posterior_vector`
- `vol_state`
- `state_dwell_sec`
- `model_version`

### hmm_transition_log.csv
- `ts`
- `from_state`
- `to_state`
- `confidence`
- `margin`
- `confirmation_reason`

---

## 11. Invariants (Cannot Be Broken)

- HMM never issues trade direction
- HMM never adjusts trade parameters
- HMM cannot bypass Safety or Volatility
- All state changes are logged
- HMM output is explainable and replayable

---

## 12. Mental Model (Authoritative)

- Volatility answers: “Is the market tradable?”
- HMM answers: “What kind of market is this?”
- Strategy answers: “How do I trade this kind of market?”

Each layer has one job.

---

## 13. Status

**HMM Global Regime Module v1.0 — LOCKED**

This module completes the global gating bracket.