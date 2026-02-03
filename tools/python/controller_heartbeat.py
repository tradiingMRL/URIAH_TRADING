import json
import time
from datetime import datetime, timezone
from pathlib import Path

HEALTH_DIR = Path("data/live/health")
HEARTBEAT_FILE = HEALTH_DIR / "controller_heartbeat.json"
INTERVAL_SEC = 5


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main():
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    print("Controller heartbeat started. Ctrl+C to stop.")

    while True:
        try:
            payload = {
                "ts_utc": utc_now(),
                "status": "OK",
                "source": "python_controller",
            }
            HEARTBEAT_FILE.write_text(
                json.dumps(payload),
                encoding="utf-8"
            )
        except Exception:
            # Silent by design; NT8 detects staleness instead
            pass

        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()