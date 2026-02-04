from contracts.enums import MarketRegime, TradePermission
from contracts.messages import MarketFeatures
from contracts.state import MarketState

from modules.safety_gate import SafetyGate
from modules.volatility_gate import VolatilityGate
from modules.hmm_gate import HMMGate
from modules.early_exit import EarlyExit


class Orchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.safety = SafetyGate((config or {}).get("safety", {}))
        self.volatility = VolatilityGate((config or {}).get("volatility", {}))
        self.hmm = HMMGate((config or {}).get("hmm", {}))
        self.early_exit = EarlyExit((config or {}).get("early_exit", {}))

    def step(self, features: MarketFeatures) -> MarketState:
        # 1) SAFETY (absolute)
        s = self.safety.check(features)
        if not s.ok:
            return MarketState(
                timestamp=features.timestamp,
                instrument=features.instrument,
                regime=MarketRegime.HALT,
                permission=TradePermission.BLOCK,
                safety_ok=False,
                volatility_ok=False,
                early_exit_active=False,
                confidence=0.0,
                reason=f"SAFETY:{s.reason}",
            )

        # 2) VOLATILITY (permission governance)
        v = self.volatility.check(features)
        if not v.ok:
            perm = TradePermission.REDUCE if v.permission == "REDUCE" else TradePermission.BLOCK
            return MarketState(
                timestamp=features.timestamp,
                instrument=features.instrument,
                regime=MarketRegime.CHAOTIC,
                permission=perm,
                safety_ok=True,
                volatility_ok=False,
                early_exit_active=False,
                confidence=0.0,
                reason=f"VOL:{v.reason}",
            )

        # 3) HMM (regime owner)
        h = self.hmm.infer(features)

        # 4) EARLY EXIT (downgrade-only)
        ee = self.early_exit.check(features)
        perm = TradePermission.ALLOW
        if ee.permission == "REDUCE":
            perm = TradePermission.REDUCE
        elif ee.permission == "BLOCK":
            perm = TradePermission.BLOCK

        return MarketState(
            timestamp=features.timestamp,
            instrument=features.instrument,
            regime=h.regime,
            permission=perm,
            safety_ok=True,
            volatility_ok=True,
            early_exit_active=bool(ee.active),
            confidence=float(h.confidence),
            reason=f"HMM:{h.reason}|EE:{ee.reason}",
        )