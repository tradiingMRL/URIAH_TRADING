import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_file: Path, level: str = "INFO"):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Clear any existing handlers (important for re-runs)
    logger.handlers.clear()

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5_000_000,
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger