URIAH_TRADING — Volatility Gate v1.0
===================================

Purpose
-------
Define a standalone Volatility Gate that controls WHEN the market
is tradable, not WHAT to trade.

This gate is:
- ENTRY VETO ONLY
- POST-ENTRY WEIGHTING FACTOR ONLY
- NEVER a trade generator
- NEVER a forced exit by itself

Volatility is treated as a TIME + VELOCITY problem, not a bar-size problem.

------------------------------------------------------------

1) Authority & Constraints
--------------------------

Authority:
- Entry: ABSOLUTE VETO
- Post-entry: WEIGHTING FACTOR ONLY

Hard prohibitions:
- ❌ Volatility may not generate entries
- ❌ Volatility may not force exits alone
- ❌ Volatility may not override Safety Gate

------------------------------------------------------------

2) Core Principle
-----------------

The dangerous form of volatility is NOT “large movement”,
but movement that is:

- Too FAST relative to the trade’s required progress, or
- Too ERRATIC relative to structure and time remaining

Volatility is therefore evaluated in terms of:
- Velocity
- Time feasibility
- Coherence

------------------------------------------------------------

3) Primary Volatility Measures (NON-ATR)
----------------------------------------

### 3.1 Observed Velocity vs Required Velocity

Definitions:

Observed Velocity:
  V_obs = |ΔPrice| / ΔTime

Required Velocity:
  V_req = Distance_to_Target / Time_Remaining

Interpretation:

- V_obs >> V_req
    → Market is moving too fast
    → Indicates instability / snapback risk
    → ENTRY VETO

- V_obs << V_req
    → Market too slow
    → Trade becoming time-infeasible
    → POST-ENTRY WEIGHTING ↑

- V_obs ≈ V_req
    → Healthy, tradable volatility

This comparison is CENTRAL to the volatility gate.

------------------------------------------------------------

### 3.2 Time-Compressed Displacement

Purpose:
Detect excessive meaningful price movement in too little time.

Conceptual Measure:

  Displacement_Ratio =
    |Price_now − Price_t−N| / Expected_Displacement_for_N

Where:
- N is short (e.g. 30s, 1m, 3m)
- Expected_Displacement_for_N is derived from recent realised movement
  (NOT ATR)

Interpretation:

- Large displacement in short time
    → Structural instability
    → ENTRY VETO

- Moderate displacement with follow-through
    → Tradable

------------------------------------------------------------

### 3.3 Coherence Filter (Critical)

Fast movement is acceptable ONLY if it is coherent.

Coherence indicators (examples):
- Directional persistence (not back-and-forth)
- Respect of structure (box, EVWAP, VWAP mean)
- Absence of violent immediate retracement
- L2 confirms continuation or exhaustion (system-dependent)

Rules:
- High velocity WITHOUT coherence → ENTRY VETO
- Coherence loss post-entry → WEIGHTING FACTOR ↑

------------------------------------------------------------

4) Volatility Regimes
---------------------

The gate classifies volatility into:

- PERMITTED
- ELEVATED
- HOSTILE

HOSTILE volatility characteristics:
- V_obs >> V_req
- Extreme displacement in short time
- Low coherence
- Time feasibility collapse

HOSTILE → ENTRY DENIED (all systems)

------------------------------------------------------------

5) System Sensitivity
---------------------

### System A — Breakout + Continuation

Requires:
- Velocity sufficient but not excessive
- Coherent movement away from structure
- Time feasibility ≥ minimum TP requirement

Rejects:
- Explosive moves with no continuation structure
- Whipsaw velocity

------------------------------------------------------------

### System B — Mean Reversion

Requires:
- Velocity exhaustion
- Deceleration
- L2 confirmation of absorption

Rejects:
- Accelerating velocity
- Trend-aligned volatility

------------------------------------------------------------

6) Post-Entry Behaviour (Weighting Only)
----------------------------------------

If volatility regime changes after entry:

Increase early-exit weighting when:
- Velocity accelerates against premise
- Time remaining becomes insufficient
- Coherence deteriorates

Decrease early-exit weighting when:
- Velocity stabilises
- Coherence improves
- Price progresses toward TP

Rules:
- No immediate exits
- No single volatility signal is sufficient
- Must combine with kitbag factors

------------------------------------------------------------

7) Relationship to HMM
----------------------

- Volatility and HMM are independent
- Both may veto entry
- Both may contribute post-entry weighting
- Neither may force exit alone

------------------------------------------------------------

8) ATR Clarification
--------------------

ATR is:
- A descriptive normalisation tool only
- Useful for expressing distances
- NOT a volatility decision trigger

ATR must never be used as a sole gate.

------------------------------------------------------------

9) Logging Requirements
-----------------------

At entry:
- Observed velocity
- Required velocity
- Displacement metrics
- Coherence outcome
- Volatility regime

Post-entry:
- Regime changes
- Contribution to early-exit score

------------------------------------------------------------

Versioning
----------
v1.0 — Initial velocity-based volatility gate
Changes require explicit commit + version bump.