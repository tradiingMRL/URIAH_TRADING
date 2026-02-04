# modules/safety_gate.py

from dataclasses import dataclass
from typing import Optional

from contracts.messages import MarketFeatures


@dataclass(frozen=True)
class SafetyDecision:
    ok: bool
    reason: str


class SafetyGate:
    """
    Safety Gate (v1):
    - Designed to be fail-closed.
    - For now, this is a structured stub that always passes unless configured otherwise.

    Later, this is where we wire:
    - session/time permissions
    - max daily loss / DD lockouts
    - connection health / stale feed checks
    - one-position-at-a-time / governance locks
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.force_halt: bool = bool(self.config.get("force_halt", False))
        self.force_halt_reason: str = str(self.config.get("force_halt_reason", "forced_halt"))

    def check(self, features: MarketFeatures) -> SafetyDecision:
        if self.force_halt:
            return SafetyDecision(ok=False, reason=self.force_halt_reason)

        return SafetyDecision(ok=True, reason="safety_ok_v1_stub")