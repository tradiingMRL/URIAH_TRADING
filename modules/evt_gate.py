from dataclasses import dataclass

from contracts.messages import MarketFeatures


@dataclass(frozen=True)
class EVTDecision:
    ok: bool
    reason: str


class EVTGate:
    """
    Expected Viability Test (EVT) - STUB.

    Later:
      - Use velocity + acceleration + distance-to-target
      - Check TP-in-time plausibility
      - Used both at entry and during open trades (behavioural decay)

    Current stub:
      - enabled false => always OK
      - enabled true => requires abs(velocity) >= min_velocity
    """

    def __init__(self, config: dict):
        cfg = config or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.min_velocity = float(cfg.get("min_velocity", 0.0))

    def check(self, features: MarketFeatures) -> EVTDecision:
        if not self.enabled:
            return EVTDecision(True, "evt_disabled_stub")

        if abs(float(features.velocity)) < self.min_velocity:
            return EVTDecision(False, "evt_velocity_too_low")

        return EVTDecision(True, "evt_ok")