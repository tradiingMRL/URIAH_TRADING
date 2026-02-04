# logging/event_logger.py

class EventLogger:
    """
    Stub logger.
    Will later write structured events to CSV / Parquet / DB.
    """

    def __init__(self, config: dict):
        self.config = config

    def log_features(self, features):
        # placeholder
        pass

    def log_state(self, state):
        # placeholder
        pass