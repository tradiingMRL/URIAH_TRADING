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