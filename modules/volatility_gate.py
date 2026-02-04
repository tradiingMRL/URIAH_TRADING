from dataclasses import dataclass
from contracts.messages import MarketFeatures


@dataclass(frozen=True)
class VolatilityDecision:
    ok: bool
    permission: str   # "ALLOW" | "REDUCE" | "BLOCK"
    reason: str


class VolatilityGate:
    """
    Volatility Gate (v1):
    Uses precomputed non-ATR volatility metric: features.vol_norm.
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.threshold_ok = float(self.config.get("threshold_ok", 1.0))
        self.threshold_block = float(self.config.get("threshold_block", 1.5))
        if self.threshold_block < self.threshold_ok:
            raise ValueError("threshold_block must be >= threshold_ok")

    def check(self, features: MarketFeatures) -> VolatilityDecision:
        v = float(features.vol_norm)

        if v <= self.threshold_ok:
            return VolatilityDecision(True, "ALLOW", "vol_ok")

        if v <= self.threshold_block:
            return VolatilityDecision(False, "REDUCE", "vol_high_reduce")

        return VolatilityDecision(False, "BLOCK", "vol_extreme_block")