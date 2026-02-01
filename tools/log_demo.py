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