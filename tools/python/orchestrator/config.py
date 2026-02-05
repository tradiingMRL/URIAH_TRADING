from pathlib import Path

# ---------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------

# Root of the project (adjust parents[] only if structure changes)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = PROJECT_ROOT / "data"
HEALTH_DIR = DATA_DIR / "live" / "health"
HEALTH_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------

ENV = "DEV"          # DEV | PROD
DRY_RUN = False

# ---------------------------------------------------------------------
# Orchestrator timing
# ---------------------------------------------------------------------

HEARTBEAT_SEC = 1.0
SHUTDOWN_GRACE_SEC = 5.0

HEARTBEAT_FILE = HEALTH_DIR / "orchestrator_heartbeat.json"

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

LOG_LEVEL = "INFO"
LOG_FILE = LOG_DIR / "orchestrator.log"