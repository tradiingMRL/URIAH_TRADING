# URIAH_TRADING — Instrument Resolution Module v1.0 (LOCKED)

## 1. Purpose
This module defines how URIAH_TRADING identifies, resolves, and validates
tradable instruments so that the system **never breaks at contract expiry**.

All logic operates on a **root instrument** (e.g. MES).
Execution occurs on a **resolved active contract** (e.g. MES 06-26).

No component may hard-code contract expiry months.

---

## 2. Core Definitions (Authoritative)

### 2.1 Root Instrument
A perpetual identifier representing the product family.

Examples:
- `MES`
- `ES`
- `NQ`
- `YM`

The root instrument is used by:
- strategy logic
- volatility analysis
- HMM regime inference
- analytics and reporting

---

### 2.2 Active Contract
The specific futures contract currently being traded.

Examples:
- `MES 03-26`
- `MES 06-26`

The active contract:
- is determined at runtime
- may change over time (rollover)
- must be consistent across all system components

---

### 2.3 Front Contract
The contract designated as the **current tradable front month**.

**Source of truth (v1.0):**
- NinjaTrader 8 execution layer

Python must never guess the front contract if NT8 can report it.

---

## 3. System-Wide Invariants (Non-Negotiable)

- No module may assume a fixed contract expiry
- All messages must carry both:
  - `instrument.root`
  - `instrument.contract`
- All logs must record both root and contract
- Strategy logic operates on root, not expiry
- Execution always occurs on the active contract
- Contract mismatches block entries

---

## 4. Instrument Object (Canonical Form)

All inter-process messages must include:

```json
"instrument": {
  "root": "MES",
  "contract": "MES 06-26",
  "exchange": "CME"
}
