# modules/hmm_gate.py

from dataclasses import dataclass

from contracts.enums import MarketRegime
from contracts.messages import MarketFeatures


@dataclass(frozen=True)
class HMMDecision:
    regime: MarketRegime
    confidence: float
    reason: str


class HMMGate:
    """
    HMM Gate (stub v1):
    - Alternates TREND / MEAN_REVERSION for plumbing proof.
    - Confidence is deterministic and stable (0.55 / 0.60).
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.enabled: bool = bool(self.config.get("enabled", True))
        self.stub_mode: str = str(self.config.get("stub_mode", "alternating"))
        self._tick = 0

    def infer(self, features: MarketFeatures) -> HMMDecision:
        if not self.enabled:
            return HMMDecision(
                regime=MarketRegime.CHAOTIC,
                confidence=0.0,
                reason="hmm_disabled",
            )

        if self.stub_mode == "alternating":
            self._tick += 1
            if self._tick % 2 == 1:
                return HMMDecision(MarketRegime.TREND, 0.60, "hmm_stub_trend")
            return HMMDecision(MarketRegime.MEAN_REVERSION, 0.55, "hmm_stub_mr")

        # default stub behavior
        return HMMDecision(
            regime=MarketRegime.CHAOTIC,
            confidence=0.0,
            reason="hmm_stub_chaotic",
        )