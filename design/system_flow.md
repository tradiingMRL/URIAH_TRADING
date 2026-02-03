# URIAH_TRADING â€” System Flow (v1)

This document defines the **runtime decision and control flow** of the URIAH_TRADING system.
It is architectural and binding.

---

## 1. Execution Model

- Logic updates occur on **1-minute bars**
- Execution management operates on **ticks**
- Only one position may be open at a time
- Uncertainty defaults to **NO TRADE**

---

## 2. High-Level Runtime Flow
Market Data (Rithmic)
â†“
Layer 0: Market Hostility Overlay
(trade-outcome dynamics + Monte Carlo tails)
â†“
Layer 1: HMM Regime Gate
(global market state)
â†“
Strategy Setup Detection
(System A / System B)
â†“
Entry Decision Gates
(price, volume, velocity, time-to-TP)
â†“
Trade Lifecycle
(INTENT â†’ ENTRY â†’ MANAGE â†’ EXIT)
â†“
Post-Trade Accounting
(PnL, time debt, belief updates)
â†“
Logging & Persistence
(NDJSON â†’ future DB)

---
## 3. Layer 0 â€” Market Hostility Overlay

Purpose:
- Detect hostile market conditions not visible in price structure alone
- Prevent repeated losses during adverse regimes

### Inputs (from trade log only)
- trade_end_time
- R (R-multiple)
- is_loss = (R < 0)

### Live Metrics
- k_live(W): number of losing trades in last W minutes
- LCR(t): k_live(W) / W
- Î”LCR: slope of LCR
- Î”Î”LCR: acceleration of LCR
- L_live: current losing streak length

### Monte Carlo Baselines
- clustering tails: K95(W), K99(W)
- optional streak tails: LS95(N), LS99(N)

### Outputs
- HOSTILITY_STATE âˆˆ {NORMAL, ELEVATED, HOSTILE}
- optional forward projections (e.g. TTH, P_HOSTILE)

### Decision Logic

PRECHECK: sufficient evidence?
NO  â†’ HOSTILITY_STATE = NORMAL
YES â†’ evaluate dynamics

NODE A: Î”Î”LCR strongly positive?
YES â†’ check tails
NO  â†’ NODE B

NODE B: Î”LCR mildly positive?
YES â†’ ELEVATED
NO  â†’ NORMAL

NODE C: tail extreme?
YES â†’ HOSTILE (pause new trades + cooldown)
NO  â†’ ELEVATED

---

## 4. Layer 1 â€” HMM Regime Gate

Purpose:
- Classify global market state
- Permit or veto entry attempts
- Contribute to belief decay during open trades

### Inputs
- 1-minute bars (primary)
- 15-minute bars (context)
- optional bid/ask features

### Outputs
- regime_state (e.g. CHOP, EXITING_CHOP, EXPANSION, MEAN_REVERSION)
- confidence
- state_probs

### Role
- If regime unsuitable â†’ **VETO ENTRY**
- If regime deteriorates during trade â†’ **belief decay signal**

---

## 5. Entry Decision Tree (FLAT State Only)

FLAT
â†“
NODE 0: Setup exists?
NO  â†’ DO NOTHING
YES â†’ NODE 1

NODE 1: HMM permission?
NO  â†’ DO NOT ENTER
YES â†’ NODE 2

NODE 2: Gross margin test?
(fixed stop + fixed TP acceptable)
NO  â†’ DO NOT ENTER
YES â†’ NODE 3

NODE 3: Expected viability test
(velocity / acceleration â†’ TP-in-time plausible)
NO  â†’ DO NOT ENTER
YES â†’ ENTER TRADE

---

## 6. In-Trade Management & Exit Logic

TRADE OPEN
â†“
NODE 0: Hard stop hit?
YES â†’ IMMEDIATE EXIT
NO  â†’ NODE 1

NODE 1: Behavioural failure?
(time vs progress, velocity decay)
YES â†’ EXIT
NO  â†’ NODE 2

NODE 2: Context degradation?
(HMM belief deteriorating)
YES â†’ elevate exit risk
NO  â†’ NODE 3

NODE 3: Retracement risk excessive?
YES â†’ EXIT
NO  â†’ CONTINUE HOLD

---

## 7. Separation of Concerns (Hard Rules)

- Strategies propose setups only
- Gates permit or veto actions
- Lifecycle owns trade state
- Execution executes orders only
- No module may override a veto

---

## 8. Change Control

Any change to this file requires:
- Explicit discussion
- Same-day git commit


