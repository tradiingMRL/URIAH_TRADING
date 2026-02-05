from __future__ import annotations

from dataclasses import dataclass

from tools.python.common.events import SignalEvent
from tools.python.common.market_state import (
    MarketState,
    MarketFeatures,
    TradePermission,
    MarketRegime,
)


@dataclass(frozen=True)
class RouterConfig:
    # Conservative until your real gating is plugged in
    min_confidence_to_trade: float = 0.55


class Router:
    """
    Router consumes:
      - MarketFeatures (raw descriptors)
      - MarketState (regime + permission + gates)

    And outputs:
      - SignalEvent (BUY/SELL/HOLD) with reasons

    Router does NOT place orders.
    It only decides "who may act" and "whether action is allowed".
    """

    def __init__(self, cfg: RouterConfig | None = None):
        self.cfg = cfg or RouterConfig()

    def route(self, feats: MarketFeatures, state: MarketState) -> SignalEvent:
        # ------------------------------------------------------------
        # 1) HARD VETO LAYER (non-negotiable)
        # ------------------------------------------------------------
        if state.permission == TradePermission.BLOCK:
            return SignalEvent(
                timestamp=feats.timestamp,
                instrument=feats.instrument,
                strategy="Router",
                action="HOLD",
                strength=0.0,
                reason=f"router_veto_permission_BLOCK:{state.reason}",
                tag="veto",
            )

        if not state.safety_ok:
            return SignalEvent(
                timestamp=feats.timestamp,
                instrument=feats.instrument,
                strategy="Router",
                action="HOLD",
                strength=0.0,
                reason=f"router_veto_safety_not_ok:{state.reason}",
                tag="veto",
            )

        if not state.volatility_ok:
            return SignalEvent(
                timestamp=feats.timestamp,
                instrument=feats.instrument,
                strategy="Router",
                action="HOLD",
                strength=0.0,
                reason=f"router_veto_volatility_not_ok:{state.reason}",
                tag="veto",
            )

        # ------------------------------------------------------------
        # 2) SOFT VETO LAYER (conservative)
        # ------------------------------------------------------------
        if state.confidence < self.cfg.min_confidence_to_trade:
            return SignalEvent(
                timestamp=feats.timestamp,
                instrument=feats.instrument,
                strategy="Router",
                action="HOLD",
                strength=0.0,
                reason=f"router_hold_low_confidence:{state.confidence:.3f}:{state.reason}",
                tag="soft_veto",
            )

        # ------------------------------------------------------------
        # 3) ROUTE BY REGIME (placeholder mapping)
        # ------------------------------------------------------------
        if state.regime == MarketRegime.TREND:
            return SignalEvent(
                timestamp=feats.timestamp,
                instrument=feats.instrument,
                strategy="SystemB",
                action="HOLD",
                strength=state.confidence,
                reason=f"router_route_trend_to_SystemB:{state.reason}",
                tag="route",
            )

        if state.regime == MarketRegime.MEAN_REVERSION:
            return SignalEvent(
                timestamp=feats.timestamp,
                instrument=feats.instrument,
                strategy="SystemC",
                action="HOLD",
                strength=state.confidence,
                reason=f"router_route_mr_to_SystemC:{state.reason}",
                tag="route",
            )

        # Default: do nothing
        return SignalEvent(
            timestamp=feats.timestamp,
            instrument=feats.instrument,
            strategy="Router",
            action="HOLD",
            strength=0.0,
            reason=f"router_hold_regime_{state.regime.value}:{state.reason}",
            tag="hold",
        )