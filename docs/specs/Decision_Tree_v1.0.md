URIAH_TRADING — Decision Tree v1.0
=================================

Purpose
-------
This document defines the binding decision tree for URIAH_TRADING.
It governs:
- Entry permission
- Trade management
- Early exit eligibility
- Absolute prohibitions

This document is RULES, not implementation.

Key Principle
-------------
“Gates veto; systems decide.”

- Global gates NEVER generate trades.
- Global gates MAY veto entry.
- Mid-trade global state changes are WEIGHTING FACTORS ONLY.
- Safety overrides everything.

------------------------------------------------------------

1) Entry-Time Decision Tree (Strict Order)
------------------------------------------

Entry evaluation is performed ONLY at the moment an entry is proposed.

### Gate Order (LOCKED)

1. Safety Gate (absolute)
2. Volatility Gate
3. HMM Global State Gate
4. System-Specific Rules (A or B)

If ANY gate fails → ENTRY DENIED.

------------------------------------------------------------

2) Gate Definitions
-------------------

### 2.1 Safety Gate (ABSOLUTE)

Inputs:
- NT8 connection state
- Rithmic connection state
- Python controller heartbeat
- Active lockout flag

Rules:
- If NOT SAFE → ENTRY DENIED
- If lockout_active = 1 → ENTRY DENIED

This gate has:
- Absolute veto power
- Force-flat authority (outside of entry context)

------------------------------------------------------------

### 2.2 Volatility Gate (ENTRY VETO ONLY)

Purpose:
- Prevent trading during unrestrained / hostile volatility regimes

Inputs (examples, not exhaustive):
- ATR expansion ratios
- Range spikes
- Volatility-of-volatility
- Session-relative volatility metrics

Rules:
- If volatility regime = NOT PERMITTED → ENTRY DENIED
- Volatility gate NEVER generates entries

Post-entry:
- Volatility regime changes MAY increase early-exit weighting
- Volatility ALONE may not force exit

------------------------------------------------------------

### 2.3 HMM Global State Gate (ENTRY VETO ONLY)

States:
- CHOP
- BREAKOUT_WINDOW
- LATE_TREND

Rules:
- HMM NEVER directs trades
- HMM NEVER triggers entries
- HMM may veto entry depending on system + state compatibility

Examples:
- System A may require BREAKOUT_WINDOW
- System B may require non-trending exhaustion conditions

Post-entry:
- State transitions MAY affect early-exit weighting
- HMM state change ALONE may not force exit

------------------------------------------------------------

3) System-Specific Entry Rules
------------------------------

### 3.1 System A — Breakout + Continuation

Characteristics:
- Fixed position size
- Fixed SL / TP at entry
- No scale-ins
- No order modification

Entry eligibility:
- Price breaks defined structure (box / range)
- Break occurs within allowed distance (e.g. ≤ 0.5 × ATR from structure)
- Risk parameters satisfied

Special rule:
- Entry is permitted ONLY if continuation feasibility exists
  (minimum projected continuation ≥ TP distance)

------------------------------------------------------------

### 3.2 System B — Mean Reversion

Characteristics:
- Trades against prevailing move
- Requires stronger confirmation of exhaustion
- L2 data has elevated importance

Entry eligibility:
- Evidence of exhaustion / absorption
- Mean-reversion zone validity
- L2 confirms weakening continuation pressure

------------------------------------------------------------

4) Trade Management (Post-Entry)
--------------------------------

Once a trade is live:

- NO gate may retroactively cancel the trade
- NO gate may directly kill the trade

Management decisions are made via a WEIGHTED KITBAG.

------------------------------------------------------------

5) Early Exit Eligibility (Kitbag Model)
----------------------------------------

Early exit MAY be considered when multiple factors align.

Possible contributors:
- Time feasibility degradation
- Failure to progress toward TP
- EVWAP / proximity-weighted VWAP retracement
- L2 deterioration
- Volatility regime change
- HMM state change
- Order flow imbalance loss

Rules:
- No single factor is sufficient by itself
- Exit requires cumulative weight crossing threshold
- All exits must be explainable in logs

------------------------------------------------------------

6) Exit Types
-------------

Permitted exits:
- Stop Loss (SL)
- Take Profit (TP)
- Early Exit (Kitbag-qualified)

Forbidden exits:
- HMM-only exit
- Volatility-only exit
- Manual discretionary exit (outside testing)

------------------------------------------------------------

7) Absolute Prohibitions
-----------------------

- ❌ No scale-ins
- ❌ No order modifications
- ❌ No averaging
- ❌ No re-entries after force-flat until reset
- ❌ No trading during lockout
- ❌ No trades without passing ALL entry gates

------------------------------------------------------------

8) Logging & Audit Requirements
-------------------------------

For every entry decision:
- Gate pass/fail must be logged
- Gate reason codes must be logged

For every early exit:
- Contributing factors must be logged
- Dominant reason must be identifiable

------------------------------------------------------------

Versioning
----------
v1.0 — Initial binding decision tree
Changes require explicit commit + version bump.