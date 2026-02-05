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

    Stub modes:
      - "alternating": TREND, MEAN_REVERSION, TREND, MEAN_REVERSION...
      - "trend_only": always TREND (useful to test SystemA only)
      - "mr_only": always MEAN_REVERSION (useful to test SystemB only)
      - anything else: CHAOTIC

    This gate owns "regime" and "confidence" only.
    It does NOT set permission.
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

        mode = self.stub_mode.lower().strip()

        if mode == "trend_only":
            return HMMDecision(
                regime=MarketRegime.TREND,
                confidence=0.60,
                reason="hmm_stub_trend_only",
            )

        if mode == "mr_only":
            return HMMDecision(
                regime=MarketRegime.MEAN_REVERSION,
                confidence=0.55,
                reason="hmm_stub_mr_only",
            )

        if mode == "alternating":
            self._tick += 1
            if self._tick % 2 == 1:
                return HMMDecision(
                    regime=MarketRegime.TREND,
                    confidence=0.60,
                    reason="hmm_stub_trend",
                )
            return HMMDecision(
                regime=MarketRegime.MEAN_REVERSION,
                confidence=0.55,
                reason="hmm_stub_mr",
            )

        return HMMDecision(
            regime=MarketRegime.CHAOTIC,
            confidence=0.0,
            reason="hmm_stub_chaotic",
        )