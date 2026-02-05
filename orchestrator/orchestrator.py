import json
from pathlib import Path

from modules.hostility_overlay import HostilityOverlay, HostilityState
from modules.safety_gate import SafetyGate
from modules.volatility_gate import VolatilityGate
from modules.hmm_gate import HMMGate
from modules.early_exit import EarlyExit
from modules.daily_loss_gate import DailyLossGate
from modules.time_debt_gate import TimeDebtGate

from contracts.messages import MarketFeatures
from contracts.state import MarketState
from contracts.enums import MarketRegime, TradePermission

from tools.python.orchestrator.config import HEARTBEAT_FILE


class Orchestrator:
    def __init__(self, config: dict):
        self.config = config or {}

        # Core safety & governance
        self.safety = SafetyGate(self.config.get("safety", {}))
        self.daily_loss = DailyLossGate(self.config.get("daily_loss", {}))
        self.time_debt = TimeDebtGate(self.config.get("time_debt", {}))
        self.hostility = HostilityOverlay(self.config.get("hostility", {}))
        self.volatility = VolatilityGate(self.config.get("volatility", {}))

        # Market intelligence
        self.hmm = HMMGate(self.config.get("hmm", {}))
        self.early_exit = EarlyExit(self.config.get("early_exit", {}))

    # ------------------------------------------------------------------
    # Heartbeat (external health / monitoring)
    # ------------------------------------------------------------------
    def _write_heartbeat(self, features: MarketFeatures, state: MarketState) -> None:
        p = Path(HEARTBEAT_FILE)
        p.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "ts": features.timestamp.isoformat(),
            "instrument": features.instrument,
            "price": float(getattr(features, "price", 0.0)),
            "regime": state.regime.value,
            "permission": state.permission.value,
            "reason": state.reason,
            "safety_ok": bool(state.safety_ok),
            "volatility_ok": bool(state.volatility_ok),
            "early_exit_active": bool(state.early_exit_active),
            "confidence": float(state.confidence),
        }

        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(p)

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------
    def step(self, features: MarketFeatures) -> MarketState:

        # 1) SAFETY — absolute fail-closed
        s = self.safety.check(features)
        if not s.ok:
            ms = MarketState(
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
            self._write_heartbeat(features, ms)
            return ms

        # 2) DAILY LOSS — hard stop
        dl = self.daily_loss.check()
        if not dl.ok:
            ms = MarketState(
                timestamp=features.timestamp,
                instrument=features.instrument,
                regime=MarketRegime.HALT,
                permission=TradePermission.BLOCK,
                safety_ok=True,
                volatility_ok=False,
                early_exit_active=False,
                confidence=0.0,
                reason=f"DAILYLOSS:{dl.reason}",
            )
            self._write_heartbeat(features, ms)
            return ms

        # 3) TIME DEBT — ALLOW or BLOCK only (no REDUCE)
        td = self.time_debt.check()
        if not td.ok:
            ms = MarketState(
                timestamp=features.timestamp,
                instrument=features.instrument,
                regime=MarketRegime.HALT,
                permission=TradePermission.BLOCK,
                safety_ok=True,
                volatility_ok=False,
                early_exit_active=False,
                confidence=0.0,
                reason=f"TIMEDEBT:{td.reason}",
            )
            self._write_heartbeat(features, ms)
            return ms

        # 4) HOSTILITY OVERLAY — governance veto
        ho = self.hostility.evaluate(features)
        if ho.state == HostilityState.HOSTILE:
            ms = MarketState(
                timestamp=features.timestamp,
                instrument=features.instrument,
                regime=MarketRegime.HALT,
                permission=TradePermission.BLOCK,
                safety_ok=True,
                volatility_ok=False,
                early_exit_active=False,
                confidence=0.0,
                reason=f"HOSTILITY:{ho.reason}",
            )
            self._write_heartbeat(features, ms)
            return ms

        # 5) VOLATILITY — governance veto (no reduce sizing)
        v = self.volatility.check(features)
        if not v.ok:
            ms = MarketState(
                timestamp=features.timestamp,
                instrument=features.instrument,
                regime=MarketRegime.CHAOTIC,
                permission=TradePermission.BLOCK,
                safety_ok=True,
                volatility_ok=False,
                early_exit_active=False,
                confidence=0.0,
                reason=f"VOL:{v.reason}",
            )
            self._write_heartbeat(features, ms)
            return ms

        # 6) HMM — regime owner
        h = self.hmm.infer(features)

        # 7) EARLY EXIT — downgrade only to BLOCK
        ee = self.early_exit.check(features)
        perm = TradePermission.ALLOW
        if ee.permission == "BLOCK":
            perm = TradePermission.BLOCK

        ms = MarketState(
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

        self._write_heartbeat(features, ms)
        return ms