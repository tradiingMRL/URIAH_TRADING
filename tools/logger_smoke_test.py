# tools/logger_smoke_test.py
import sys
from pathlib import Path

# Ensure repo root is on sys.path so imports work from /tools
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.core.logger import NDJSONLogger


def main():
    logger = NDJSONLogger(Path("logs/events.ndjson"))
    logger.log(
        event_type="SYSTEM_START",
        severity="INFO",
        module="SYSTEM",
        message="logger smoke test ok",
        correlation_id="SYS_20260202",
    )
    print("LOGGER SMOKE TEST OK")


if __name__ == "__main__":
    main()