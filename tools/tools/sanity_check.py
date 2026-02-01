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
        f.write(json.dumps(payload) + "\n")

    print("[PASS] sanity_check complete")

if __name__ == "__main__":
    main()
