# URIAH_TRADING — Early Exit Engine v1.0 (LOCKED)

## 1. Purpose
The Early Exit Engine is the core risk-control layer that decides one thing only:

- `PERSIST` (stay in trade unchanged), or
- `EXIT_EARLY` (exit immediately via defined early-exit command)

It exists to:
- prevent catastrophic loss before SL when conditions invalidate the thesis
- preserve open profits when the thesis collapses
- enforce disciplined exits without trade-mechanic tuning

---

## 2. Non-Negotiable Constraints
Once in a trade (System A or System B), there is **no trade management**.

The Early Exit Engine never changes:
- trailing stop distance (no trailing exists)
- break-even timing (no BE exists)
- max-hold (no max-hold exists)
- partial exits (none exist)
- SL/TP values (fixed at entry; catastrophic stop + fixed TP)

Only two lifecycle actions exist:
- remain in trade unchanged
- exit early

---

## 3. Authority & Priority
Priority is fixed:
**Safety > Volatility > HMM > Early Exit Engine > Strategy**

The Early Exit Engine:
- ❌ never places trades
- ❌ never modifies SL/TP
- ✅ may request early exit after triggers
- ✅ must log every trigger and decision

---

### Step 4 — Trigger-specific retention justification (EVWAP / Box / Zone)
- If trigger = `EVWAP_TOUCH`, retention requires the Logistic Regression Review to pass:
  - if `p_continue < P_CONTINUE_MIN` → `EXIT_EARLY` (`exit_evwap_logreg_fail`)
- If trigger ∈ {BOX_REENTRY, ZONE_REENTRY}, retention requires L2 + volume justification to pass

### T1 — HMM Hostile Transition
Trigger Exit Review when:
- HMM transition is confirmed (dwell + confirmation satisfied), AND
- new state is hostile to the open strategy

### T2 — Functional EVWAP Touch
Trigger Exit Review when:
- price touches/crosses **EVWAP_effective** (EVWAP adjusted by L2 control), AND
- touch is confirmed (anti-flicker rule), AND
- position is open 

This trigger **must** invoke the Logistic Regression Review as part of the Exit Review process.
The Logistic Regression model outputs a continuation probability used to decide `PERSIST` vs `EXIT_EARLY`.

### T3A — System A Structural Failure (Box Re-entry Close)
Trigger Exit Review when:
- price re-enters the breakout box, AND
- a bar closes inside the box

### T3B — System B Structural Failure (Zone Re-entry)
Trigger Exit Review when:
- price re-enters the mean-reversion zone (defined zone), AND
- re-entry is confirmed (anti-flicker rule)

No other triggers exist in v1.0.

---

## 5. Inputs (what the Exit Review is allowed to use)

### 5.1 Global Context
- `safety_status`
- `vol_state` (HOT / NORMAL / INERT)
- `hmm_state`, `hmm_confidence`, `hmm_margin`

### 5.2 Time–Velocity Context (core)
- `time_in_trade`
- `v_abs`, `v_var`, `v_impulse`, `v_decay`
- (optionally) `time_since_last_impulse`

### 5.3 Participation Context (justification)
- L2 participation summary (non-directional where possible)
- volume participation summary (relative, not ATR-based)

### 5.4 Structural Context (trigger-specific)
- for EVWAP trigger: `EVWAP_raw`, `EVWAP_effective`, `L2_control_score`
- for box/zone triggers: structure identifiers + confirmation flag

## 5.5 Logistic Regression Review (EVWAP Touch Only)

When Trigger = `EVWAP_TOUCH`, the Exit Review must run a Logistic Regression classification step.

### Purpose
To classify whether the current microstructure/participation conditions justify **retaining** the trade after reversion to EVWAP.

### Inputs (allowed)
The Logistic Regression model may use:
- L2 feature vector (minimal, robust)
- volume participation summary
- velocity snapshot (v_abs, v_var, v_impulse, v_decay)
- structural context at EVWAP (relative position vs EVWAP_effective)

The model must not use:
- SL/TP values or distance to them
- trailing/BE logic (non-existent)
- trade PnL as an input
- future-looking price projection targets

### Output (required)
- `p_continue` ∈ [0, 1] — probability that the trade thesis remains valid / continuation is justified

### Use in Exit Review (binary)
If `p_continue < P_CONTINUE_MIN`:
- decision = `EXIT_EARLY`
- reason = `exit_evwap_logreg_fail`

Else:
- decision remains governed by the Time–Velocity Decay Model and other applicable rules
- (i.e., LogReg can veto retention; it does not force retention if time/velocity is invalid)

Explicitly excluded:
- no use of SL/TP distance
- no trailing / BE logic (non-existent)
- no trade PnL as a decision variable (may be logged, not used)

---

## 6. Decision Logic (binary only)

### Step 0 — Safety override
If `safety_status != OK`:
- decision = `EXIT_EARLY`
- reason = `exit_safety_override`

### Step 1 — Volatility context gate (no auto-exit)
Volatility never forces exit in v1.0.
It is context only. (Policy to add later if needed.)

### Step 2 — HMM hostility (global thesis collapse)
If `hmm_state ∈ {CHAOTIC, DEAD}`:
- decision = `EXIT_EARLY`
- reason = `exit_hmm_chaotic_or_dead`

If strategy–regime conflict is confirmed with sufficient confidence:
- System A open AND `hmm_state == MEAN_REVERT` AND `hmm_confidence >= CONF_REGIME_CONFLICT`
  - decision = `EXIT_EARLY`
  - reason = `exit_regime_conflict_A`
- System B open AND `hmm_state == TREND` AND `hmm_confidence >= CONF_REGIME_CONFLICT`
  - decision = `EXIT_EARLY`
  - reason = `exit_regime_conflict_B`

### Step 3 — Time–Velocity Validity (primary trade health)
A trade is valid only if BOTH are true:
- time validity = thesis progress is occurring within acceptable time
- velocity validity = continuation velocity has not decayed below acceptable level

Decision table:

| Time Valid | Velocity Valid | Decision |
|---|---|---|
| TRUE | TRUE | PERSIST |
| TRUE | FALSE | EXIT_EARLY |
| FALSE | TRUE | EXIT_EARLY |
| FALSE | FALSE | EXIT_EARLY |

If EXIT:
- reason = `exit_time_velocity_invalid`

### Step 4 — Trigger-specific justification (L2 + volume)
If trigger ∈ {EVWAP_TOUCH, BOX_REENTRY, ZONE_REENTRY}:
- require L2 + volume justification to retain the trade
- if L2+volume do NOT justify retention:
  - decision = `EXIT_EARLY`
  - reason = one of:
    - `exit_evwap_no_retention`
    - `exit_box_reentry_no_retention`
    - `exit_zone_reentry_no_retention`

If justification passes and Step 3 passes:
- decision = `PERSIST`
- reason = `persist_trigger_review_passed`

---

## 7. Outputs (single action)
The engine outputs exactly one of:
- `PERSIST`
- `EXIT_EARLY`

No other outputs exist.

---

## 8. Logging (mandatory, audit-grade)

### early_exit_log.csv (one row per trigger event)
Fields:
- `ts`
- `position_id`
- `strategy` (SystemA|SystemB)
- `trigger_type` (HMM_TRANSITION|EVWAP_TOUCH|BOX_REENTRY|ZONE_REENTRY)
- `decision` (PERSIST|EXIT_EARLY)
- `reason_code`
- `vol_state`
- `hmm_state`, `hmm_confidence`, `hmm_margin`
- `time_in_trade`
- `v_abs`, `v_var`, `v_impulse`, `v_decay`
- `L2_stress` (context)
- `L2_control_score` (if EVWAP trigger)
- `volume_participation_summary`
- `model_versions` (vol/hmm/exit)

Every decision must be explainable from logs.

---

## 9. Invariants (cannot be broken)
- No trade-mechanic mutation exists in this system.
- Early Exit Engine is binary.
- Triggers are event-driven only.
- Safety always overrides.
- Volatility blocks entries; does not exit in v1.0.
- HMM never directs trades; only veto/exit-review context.

---

## 10. Status
**Early Exit Engine v1.0 — LOCKED**

