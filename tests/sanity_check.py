from pathlib import Path
from src.core.logger import NDJSONLogger


def main():
    root = Path.cwd()
    events_log = root / "logs" / "events.ndjson"

    logger = NDJSONLogger(events_log)

    logger.write({
        "event_type": "DEMO_EVENT",
        "module": "LOGGING_TEST",
        "message": "first log write successful"
    })

    print("log_demo completed")


if __name__ == "__main__":
    main()










==================================================
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


class NDJSONLogger:
    """
    Append-only NDJSON logger.
    One event per line.
    No mutation. No deletes. Ever.
    """

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: Dict[str, Any]) -> None:
        """
        Write a single event to the log.
        Automatically injects UTC timestamp if missing.
        """
        if "ts_utc" not in event:
            event["ts_utc"] = datetime.now(timezone.utc).isoformat()

        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


def utc_now() -> str:
    """Convenience helper for explicit timestamps."""
    return datetime.now(timezone.utc).isoformat()
















================================================
## 8. System Health & Lockouts

System health logging captures **when and why trading is restricted or halted**.
These events protect capital, time, and system integrity.

### 8.1 SYSTEM_HEALTH event

**event_type:** SYSTEM_HEALTH  
**severity:** INFO | WARN | CRITICAL  
**module:** SYSTEM

Emitted whenever system health state changes.

Examples:
- data feed degradation
- execution latency
- module failure
- recovery from error

---

### 8.2 LOCKOUT_TRIGGERED event

**event_type:** LOCKOUT_TRIGGERED  
**severity:** WARN | CRITICAL  
**module:** RISK_MANAGER

This event indicates that trading has been **paused or stopped**.

---

### 8.3 Required Fields for Lockout Events

Each LOCKOUT_TRIGGERED record MUST include:

- `lockout_type`
- `lockout_reason`
- `lockout_scope` (SESSION | DAY | SYSTEM)
- `lockout_threshold`
- `lockout_current_value`

---

### 8.4 lockout_type (enumerated)

| Type | Description |
|----|-------------|
| TIME_OF_DAY | First 15 minutes / session end |
| DAILY_DRAWDOWN | High-water-mark drawdown |
| LOSING_STREAK | Losing streak escalation |
| MONTE_CARLO | MC probability breach |
| TIME_DEBT | Time-to-recovery escalation |
| SYSTEM_HEALTH | Infrastructure failure |

---

### 8.5 HEARTBEAT updates

The heartbeat file MUST be updated:
- on system start
- on system shutdown
- at a fixed interval during operation

Heartbeat includes:
- last_update_utc
- system_mode (RUNNING | PAUSED | STOPPED)
- last_critical_error (optional)

---

### 8.6 Purpose

Health and lockout logs enable:
- forensic diagnosis of downtime
- validation of risk governance
- confidence in unattended operation







===================================================

## 7. Trade Exit & Outcome Logging

Trade exits record **why** a position was closed and **what resulted**.
Exit quality is as important as entry quality.

### 7.1 TRADE_EXIT event

**event_type:** TRADE_EXIT  
**severity:** INFO  
**module:** EXECUTION_MANAGER

This event marks the **end of market exposure**.

---

### 7.2 Required Fields for TRADE_EXIT

Each TRADE_EXIT record MUST include:

- `trade_id`
- `correlation_id`
- `exit_reason_code`
- `exit_price`
- `exit_timestamp`
- `realized_pnl_usd`
- `r_multiple_realized`
- `hold_time_sec`

---

### 7.3 exit_reason_code (enumerated)

The following codes are **authoritative**:

| Code | Description |
|----|-------------|
| TARGET_HIT | Profit target reached |
| STOP_HIT | Catastrophic stop hit |
| BELIEF_DECAY | Belief fell below threshold |
| TIME_VELOCITY | Time / velocity condition failed |
| RETRACEMENT | Retracement logic triggered |
| REGIME_FLIP | HMM flipped against trade |
| TIME_LOCKOUT | Session end / forced flat |
| MANUAL | Operator intervention |
| ERROR | System error |

---

### 7.4 TRADE_SETTLED event

**event_type:** TRADE_SETTLED  
**severity:** INFO  
**module:** SYSTEM

This event finalizes attribution and analytics.
It occurs **after** TRADE_EXIT.

---

### 7.5 Required Fields for TRADE_SETTLED

Each TRADE_SETTLED record MUST include:

- `trade_id`
- `correlation_id`
- `gross_pnl_usd`
- `fees_usd`
- `net_pnl_usd`
- `margin_required_usd`
- `points_captured`
- `session_points_travelled`

---

### 7.6 Purpose

Exit and settlement logs enable:
- assessment of stop effectiveness
- identification of premature exits
- transaction cost analysis
- capital efficiency measurement










======================================================

## 6. Trade Management & Belief Decay Logging

Trade management events record **in-trade evolution** of belief, risk, and control.
They do not create signals; they explain decisions.

### 6.1 TRADE_MANAGING event

**event_type:** TRADE_MANAGING  
**severity:** INFO  
**module:** EXECUTION_MANAGER

Emitted whenever a meaningful management action or belief update occurs.

Examples:
- stop moved
- target adjusted
- trailing logic engaged
- belief score updated
- HMM state changed during trade

---

### 6.2 Required Fields for TRADE_MANAGING

Each TRADE_MANAGING record MUST include:

- `trade_id`
- `correlation_id`
- `current_price`
- `elapsed_time_sec`
- `mfe_points`
- `mae_points`
- `unrealized_pnl_usd`

---

### 6.3 Belief State Fields

These fields quantify **ongoing belief** in the trade:

- `belief_score` (0.0 – 1.0)
- `belief_trend` (IMPROVING | STABLE | DECAYING)
- `belief_decay_reason` (optional)

---

### 6.4 Regime & Structure Updates

If market state changes during a trade, the following MUST be logged:

- `hmm_regime_current`
- `hmm_direction_current`
- `hmm_confidence_current`

A **directional flip against the trade** is a critical belief event.

---

### 6.5 Purpose

These logs enable:
- diagnosis of early exits
- analysis of time / velocity failure
- validation of belief-based exits
- refinement of management rules

No trade management decision may occur **without a corresponding log record**.












==============================================================
## 5. Trade Entry Logging

A trade entry is logged only after an order is accepted and a position exists.

### 5.1 TRADE_ENTRY event

**event_type:** TRADE_ENTRY  
**severity:** INFO  
**module:** EXECUTION_MANAGER

This event marks the **official start** of a trade lifecycle.

---

### 5.2 Required Fields for TRADE_ENTRY

Each TRADE_ENTRY record MUST include:

- `trade_id`
- `correlation_id`
- `instrument`
- `direction` (LONG | SHORT)
- `contracts`
- `entry_price`
- `entry_timestamp`
- `initial_stop_price`
- `initial_target_price`
- `risk_points`
- `risk_usd`
- `expected_r_multiple`
- `expected_time_to_target_sec`

---

### 5.3 Context Fields (Recommended)

These fields are not used for execution logic but are logged for analysis:

- `hmm_regime`
- `hmm_direction`
- `hmm_confidence`
- `volatility_state`
- `velocity_state`
- `time_of_day_bucket`

---

### 5.4 Entry Attribution

TRADE_ENTRY establishes the **baseline belief** for the trade.

All later belief decay, exits, and attribution are measured
relative to this event.














=======================================================
## 4. Entry Veto Logging

Every rejected trade setup MUST be logged.
A veto is as important as a trade.

### 4.1 ENTRY_VETO event

**event_type:** ENTRY_VETO  
**severity:** INFO  
**module:** ENTRY_GATE

This event records **why a trade was not taken**, even though a setup existed.

---

### 4.2 Required Fields for ENTRY_VETO

Each ENTRY_VETO record MUST include:

- `trade_id`
- `correlation_id`
- `veto_reason_code`
- `veto_reason_detail`

---

### 4.3 veto_reason_code (enumerated)

The following codes are **authoritative**.
New codes require a contract update.

| Code | Description |
|----|-------------|
| HMM_DIRECTION | HMM disallowed trade direction |
| HMM_REGIME | Market regime not permitted |
| TIME_LOCKOUT | Session time restriction |
| DAILY_DD | Daily drawdown limit reached |
| TIME_DEBT | Time-to-recovery filter |
| VELOCITY | Velocity / acceleration gate failed |
| VOLUME | Volume confirmation failed |
| MICROSTRUCTURE | L2 / microstructure check failed |
| EXPECTANCY | Expected R / time-to-TP failed |
| SINGLE_POSITION | Existing active trade |
| SYSTEM_HEALTH | System health filter |
| MANUAL | Operator intervention |

---

### 4.4 Purpose of Veto Logging

ENTRY_VETO logs enable analysis of:
- missed opportunities
- hostile market conditions
- over-filtering
- regime mismatch
- filter redundancy

A high veto rate is **not** an error.
It is diagnostic information.




======================================================
---

### 3.2 Trade Lifecycle States

Each trade progresses through the following states in order.
Some states may be skipped, but order is preserved.

| State | Description |
|-----|-------------|
| INTENT | Setup detected, evaluation begins |
| VETOED | Trade rejected by one or more gates |
| ENTERED | Order accepted and position opened |
| MANAGING | Active trade management |
| EXITED | Position closed |
| SETTLED | Final attribution recorded |

---

### 3.3 Required Lifecycle Events

The following `event_type` values are mandatory for trade tracking:

- TRADE_INTENT
- ENTRY_VETO
- TRADE_ENTRY
- TRADE_MANAGING
- TRADE_EXIT
- TRADE_SETTLED

Each event MUST reference:
- `trade_id`
- `correlation_id`

---

### 3.4 Single-Position Rule

At most **one active trade** may exist at any time.

Rules:
- No overlapping `ENTERED` states
- New `TRADE_INTENT` is rejected if an active trade exists
- Violations are logged as `CRITICAL` severity






=================================

T20260131_0007



==================================================
## 3. Trade Identity & Lifecycle

All trade-related logging follows a **single lifecycle model**.
This allows every trade to be reconstructed deterministically.

### 3.1 trade_id
**Type:** string  
**Description:** Unique identifier for a trade.

Rules:
- Generated once at trade intent
- Stable for the entire lifecycle
- Used in both `events.ndjson` and `trades.ndjson`

Example:






=======================================================
## 2. Common Fields

All log records (across all streams) MUST include the following fields.

### 2.1 ts_utc
**Type:** string (ISO-8601)  
**Description:** Timestamp in UTC when the event was recorded.

Example:
```json
"ts_utc": "2026-01-31T03:14:15.926Z"







==============================================

## 1. Log Streams

URIAH_TRADING uses **separate log streams**, each with a single responsibility.
No log file mixes concerns.

### 1.1 events.ndjson
**Purpose:** system-level events and decisions  
**Scope:**
- system startup / shutdown
- module state changes
- veto decisions (with reason codes)
- belief decay events
- lockouts and unlocks
- errors and warnings

**File:** `logs/events.ndjson`

---

### 1.2 trades.ndjson
**Purpose:** full trade lifecycle records  
**Scope:**
- trade intent
- trade entry
- trade management updates
- trade exit
- trade outcomes and attribution

Each trade is reconstructable **end-to-end** from this file alone.

**File:** `logs/trades.ndjson`

---

### 1.3 heartbeat.txt
**Purpose:** liveness and health monitoring  
**Scope:**
- last-known alive timestamp
- last-known system mode
- last-known critical error (if any)

This file is intentionally minimal and human-readable.

**File:** `logs/heartbeat.txt`





===============================================================

# URIAH_TRADING — Logging Contract (v1)

## 1. Log Streams

URIAH_TRADING uses **separate log streams**, each with a single responsibility.
No log file mixes concerns.

### 1.1 events.ndjson
**Purpose:** system-level events and decisions  
**Scope:**
- system startup / shutdown
- module state changes
- veto decisions (with reason codes)
- belief decay events
- lockouts and unlocks
- errors and warnings

**File:** `logs/events.ndjson`

---

### 1.2 trades.ndjson
**Purpose:** full trade lifecycle records  
**Scope:**
- trade intent
- trade entry
- trade management updates
- trade exit
- trade outcomes and attribution

Each trade is reconstructable **end-to-end** from this file alone.

**File:** `logs/trades.ndjson`

---

### 1.3 heartbeat.txt
**Purpose:** liveness and health monitoring  
**Scope:**
- last-known alive timestamp
- last-known system mode
- last-known critical error (if any)

This file is intentionally minimal and human-readable.

**File:** `logs/heartbeat.txt`



=================================================================

## Purpose
This document defines the **authoritative logging schema** for URIAH_TRADING.

Logging is designed to:
- Explain **what happened** and **why**
- Support **post-trade analysis**, not signal generation
- Enable reconstruction of every trade from **womb to tomb**
- Capture **vetoes**, **belief decay**, and **system health**
- Be append-only, deterministic, and human-readable

All logs must be:
- Written as **NDJSON** (one JSON object per line)
- Timestamped in **UTC**
- Append-only (no edits, no deletes)

This contract is **stable**. Changes require an explicit version bump.









==================================================================================

findstr "__future__" tools\setup_repo.py
findstr "from future" tools\setup_repo.py





=================================================================================

#!/usr/bin/env python3
"""
URIAH_TRADING - Day 1 Foundation
Creates the agreed folder structure and minimal core files.
No external deps. Safe to re-run (idempotent).
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

TOP_LEVEL_DIRS = [
    "design",
    "design/daily",
    "src",
    "src/core",
    "config",
    "tests",
    "tests/_fixtures",
    "tools",
    "data",
    "logs",
    "out",
]

FILES = {
    ".gitignore": """\
logs/
out/
__pycache__/
*.pyc
.vscode/
data/
""",
    "design/architecture.md": """\
# URIAH_TRADING — Architecture Contract (v1)

Top-level folders are fixed.
No code may write outside logs/ or out/.
""",
    "config/app.yaml": """\
app:
  name: "URIAH_TRADING"
  timezone: "+11:00"

paths:
  data_dir: "data"
  logs_dir: "logs"
  out_dir: "out"

logging:
  events_file: "logs/events.ndjson"
  trades_file: "logs/trades.ndjson"
  heartbeat_file: "logs/heartbeat.txt"

heartbeat:
  interval_minutes: 5
""",
    "config/margin_schedule.yaml": """\
instruments:
  MES:
    rth_intraday_margin_per_contract_usd: 50
""",
    "src/core/paths.py": """\
from pathlib import Path

def find_repo_root():
    p = Path.cwd()
    for parent in [p, *p.parents]:
        if (parent / "config" / "app.yaml").exists():
            return parent
    raise RuntimeError("Repo root not found")

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
""",
    "tools/sanity_check.py": """\
from datetime import datetime, timezone
from pathlib import Path
import json

def main():
    root = Path.cwd()
    logs = root / "logs"
    logs.mkdir(exist_ok=True)

    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": "SANITY_CHECK",
        "message": "ok"
    }

    with (logs / "events.ndjson").open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\\n")

    print("[PASS] sanity_check complete")

if __name__ == "__main__":
    main()
""",
}

def main():
    root = Path.cwd()

    for d in TOP_LEVEL_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    for rel, content in FILES.items():
        p = root / rel
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

    today = datetime.now().strftime("%Y-%m-%d")
    daily = root / "design" / "daily" / f"{today}.md"
    if not daily.exists():
        daily.write_text("# Daily Notes\n", encoding="utf-8")

    print("[OK] Repo skeleton created/verified.")

if __name__ == "__main__":
    main()