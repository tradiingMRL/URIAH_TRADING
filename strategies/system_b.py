from contracts.messages import MarketFeatures
from contracts.state import MarketState
from contracts.signals import Signal


class SystemB:
    """
    System B (stub):
    - Intended for MEAN_REVERSION regime.
    - For now: always HOLD.
    """

    def __init__(self, config: dict):
        self.config = config or {}

    def decide(self, features: MarketFeatures, state: MarketState) -> Signal:
        return Signal(
            timestamp=features.timestamp,
            instrument=features.instrument,
            strategy="SystemB",
            action="HOLD",
            strength=0.0,
            reason="system_b_stub_hold",
            tag="stub",
        )