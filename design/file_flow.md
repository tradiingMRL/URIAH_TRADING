# URIAH_TRADING — File / Module Flow (v1)

This document defines **allowed module relationships**.
It is a contract, not commentary.

---

## 1. Top-Level Folders (Intent)

- `src/`  
  Core system logic (pure Python, deterministic)

- `tools/`  
  Developer utilities, demos, smoke tests  
  ❌ MUST NOT contain trading logic

- `tests/`  
  Validation and correctness checks only  
  ❌ MUST NOT generate trades

- `design/`  
  Architecture, contracts, flow diagrams

- `logs/`  
  Runtime outputs only (ignored by git)

- `config/`  
  Static configuration (YAML only)

---

## 2. Allowed Import Flow (Hard Rules)

tools  ─┐
tests  ─┼──▶ src
│
design ─┘   (NO imports into src)

### Explicit rules
- `src` MUST NOT import from:
  - `tools`
  - `tests`
  - `design`

- `tools` MAY import from:
  - `src`
  - `config`

- `tests` MAY import from:
  - `src`
  - `tools` (helpers only)

---

## 3. Current Core Modules

---

## 4. Next Planned Modules (Non-binding)

- `src/core/trade_lifecycle.py`
- `src/core/hmm_gate.py`
- `src/core/belief_state.py`

---

## 5. Change Control

Any change to this file requires:
- Explicit discussion
- Same-day git commit

## 6. Canonical Repository Scaffold (v1)

The following scaffold defines the **authoritative file layout**.
This is a design contract, not an instruction to execute blindly.

```powershell
# URIAH_TRADING – structural scaffold
# Safe to re-run. Creates folders/files only if missing.

$root = Get-Location

$dirs = @(
  "src/core/hmm",
  "src/core/time_debt",
  "src/core/health",
  "src/core/fees",
  "src/systems",
  "src/execution",
  "src/brain",
  "tests/hmm",
  "tests/systems",
  "data/raw",
  "data/derived"
)

$files = @(
  "src/core/hmm/__init__.py",
  "src/core/hmm/state_definitions.py",
  ...
)