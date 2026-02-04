from contracts.enums import MarketRegime, TradePermission
from contracts.messages import MarketFeatures
from contracts.state import MarketState

from modules.safety_gate import SafetyGate
from modules.volatility_gate import VolatilityGate


class Orchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.safety = SafetyGate((config or {}).get("safety", {}))
        self.volatility = VolatilityGate((config or {}).get("volatility", {}))

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

        # 2) VOLATILITY (non-ATR metric is precomputed as features.vol_norm)
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

        # 3) STUB until HMM/EarlyExit are added
        return MarketState(
            timestamp=features.timestamp,
            instrument=features.instrument,
            regime=MarketRegime.CHAOTIC,
            permission=TradePermission.ALLOW,
            safety_ok=True,
            volatility_ok=True,
            early_exit_active=False,
            confidence=0.0,
            reason="stub_orchestrator_v1",
        )