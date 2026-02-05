from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass(frozen=True)
class HeartbeatStatus:
    service: str
    ts_utc: str
    ok: bool
    note: str = ""


class HeartbeatWriter:
    """
    Writes a single JSON health/heartbeat file on each tick.
    Atomic write via temp file + replace (prevents partial writes).
    """

    def __init__(self, path: Path, service_name: str = "orchestrator"):
        self.path = path
        self.service_name = service_name
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def beat(self, ok: bool = True, note: str = "") -> None:
        status = HeartbeatStatus(
            service=self.service_name,
            ts_utc=datetime.now(timezone.utc).isoformat(),
            ok=ok,
            note=note,
        )
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(status.__dict__, indent=2), encoding="utf-8")
        tmp.replace(self.path)