# URIAH_TRADING — Message Contracts v1.0 (LOCKED)

## 1. Purpose
This document defines the **authoritative message contracts** between:

- **NT8 Execution Layer** (System A / System B execution)
- **Python Orchestrator** (authority: Safety, Volatility, HMM, Early Exit)
- **Risk Engines** (Volatility, HMM, Early Exit)

These contracts prevent drift and enforce invariants:
- HMM never directs trades
- No trade-mechanic mutation exists post-entry (no trailing/BE/partials/max-hold)
- Single position at a time across System A + System B
- Safety overrides everything

All messages are JSON objects with:
- `schema_version`
- `msg_type`
- `ts_utc`
- `symbol`
- `correlation_id` (UUID)

---

## 2. Transport & Delivery Rules (Implementation-Agnostic)
- Delivery mechanism may be named pipes, TCP, ZeroMQ, file drop, etc.
- Messages must be **idempotent** using `correlation_id`.
- Every request-type message must receive a response-type message unless Safety is flattening.
- All rejections must include a stable `reason_code`.

---

## 3. Global Fields (Required for all messages)

| Field | Type | Notes |
|------|------|------|
| `schema_version` | string | Must equal `"1.0"` |
| `msg_type` | string | One of the defined message types below |
| `ts_utc` | string | ISO-8601 UTC timestamp |
| `symbol` | string | Instrument identifier |
| `correlation_id` | string | UUID; unique per request/decision chain |

Optional global fields:
- `source` (e.g. `"nt8"`, `"python"`)
- `env` (e.g. `"paper"`, `"live"`)
- `notes` (free text, never parsed)

---

## 4. Message Types Overview

### NT8 → Python
1) `ENTRY_INTENT`

### Python → NT8
2) `ENTRY_PERMISSION`
3) `EARLY_EXIT_NOW`

### Internal (Python)
4) `EXIT_REVIEW_TRIGGER`
5) `EXIT_REVIEW_DECISION` (optional but recommended for auditability)
6) `POSITION_STATUS` (optional heartbeat/status)

Only the first three are required to execute the system.

---

# 5. Contracts

## 5.1 ENTRY_INTENT (NT8 → Python)

### Purpose
Sent when a strategy has a candidate entry setup and requests permission.

### Hard Rules
- NT8 must not place entry orders without an explicit `ENTRY_PERMISSION` = `ALLOW`.
- NT8 must send exactly one intent per candidate entry (no spamming).

### Schema
```json
{
  "schema_version": "1.0",
  "msg_type": "ENTRY_INTENT",
  "ts_utc": "2026-02-04T02:15:30Z",  
"instrument": {
  "root": "MES",
  "contract": "MES 03-26",
  "exchange": "CME",
  "is_front": true
}

  "correlation_id": "uuid",
  "intent_id": "uuid",
  "strategy": "SystemA|SystemB",
  "side": "LONG|SHORT",
  "entry_style": "MARKET|LIMIT|STOP",
  "proposed_entry_price": 1234.50,
  "setup_id": "string",
  "setup_context": {
    "timeframe": "string",
    "box_id": "string|null",
    "zone_id": "string|null",
    "evwap_raw": 1234.25,
    "evwap_effective": 1234.35
  },
  "risk_profile": {
    "catastrophic_sl_price": 1229.50,
    "fixed_tp_price": 1242.50
  }
}

{
  "schema_version": "1.0",
  "msg_type": "ENTRY_INTENT",
  "ts_utc": "2026-02-04T02:15:30Z",
  "symbol": "MES 03-26",
  "correlation_id": "uuid",
  "intent_id": "uuid",
  "strategy": "SystemA|SystemB",
  "side": "LONG|SHORT",
  "entry_style": "MARKET|LIMIT|STOP",
  "proposed_entry_price": 1234.50,
  "setup_id": "string",
  "risk_profile": {
    "catastrophic_sl_price": 1229.50,
    "fixed_tp_price": 1242.50
  }
}

{
  "schema_version": "1.0",
  "msg_type": "EARLY_EXIT_NOW",
  "ts_utc": "2026-02-04T02:25:10Z",
  "symbol": "MES 03-26",
  "correlation_id": "uuid",
  "position_id": "uuid",
  "strategy": "SystemA|SystemB",
  "reason_code": "string",
  "context": {
    "trigger_type": "HMM_TRANSITION|EVWAP_TOUCH|BOX_REENTRY|ZONE_REENTRY|SAFETY",
    "vol_state": "HOT|NORMAL|INERT",
    "hmm_state": "TREND|MEAN_REVERT|CHAOTIC|DEAD",
    "hmm_confidence": 0.0,
    "p_continue": 0.0
  }
}

"execution_context": {
  "expected_spread_ticks": 1,
  "liquidity_hint": "NORMAL|THIN|UNKNOWN"
}

## Execution Policy — Early Exit (Slippage Handling)

When Python issues `EARLY_EXIT_NOW`, NT8 must:
- submit an immediate, marketable exit order to flatten the full position
- prioritise execution certainty over price improvement

This is a binary risk action:
- no retries to improve price
- no scaling, partials, or staged exits
- no stop/target modification

Slippage is accepted as the cost of certainty and is recorded via `FILL_REPORT` / `EXIT_ACK`.

### Decision Finality (EXIT_EARLY)
Once the decision is `EXIT_EARLY`, the exit must be executed immediately at best available price.
No additional confirmation or price optimisation is permitted.




