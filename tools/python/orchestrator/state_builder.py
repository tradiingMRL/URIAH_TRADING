from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tools.python.common.market_state import (
    MarketFeatures,
    MarketState,
    MarketRegime,
    TradePermission,
    default_halt_state,
    default_unknown_state,
)


@dataclass(frozen=True)
class StateBuilderConfig:
    """
    Conservative defaults.
    You will later replace/extend these with your real non-ATR volatility gate + HMM.
    """
    # Volatility gate (placeholder): allow trading only when vol_norm is within bounds
    vol_norm_min: float = 0.10
    vol_norm_max: float = 0.90

    # Confidence defaults
    base_confidence: float = 0.60

    # ATR sanity (optional): if present, ensure fast/slow are positive
    require_atr_positive: bool = True


class StateBuilder:
    """
    Converts MarketFeatures -> MarketState.

    This is where *gates* live:
      - safety gating
      - volatility gating
      - (later) time-debt / news / session gating
      - (later) HMM regime + confidence
    """

    def __init__(self, cfg: StateBuilderConfig | None = None):
        self.cfg = cfg or StateBuilderConfig()

    def build(self, feats: MarketFeatures) -> MarketState:
        ts: datetime = feats.timestamp
        instrument: str = feats.instrument

        # ------------------------------------------------------------
        # 0) Basic data sanity (hard HALT if bad)
        # ------------------------------------------------------------
        if feats.price <= 0:
            return default_halt_state(ts, instrument, "BAD_DATA:price<=0")

        if feats.volume < 0:
            return default_halt_state(ts, instrument, "BAD_DATA:volume<0")

        if self.cfg.require_atr_positive:
            if feats.atr_fast is not None and feats.atr_fast <= 0:
                return default_halt_state(ts, instrument, "BAD_DATA:atr_fast<=0")
            if feats.atr_slow is not None and feats.atr_slow <= 0:
                return default_halt_state(ts, instrument, "BAD_DATA:atr_slow<=0")

        # ------------------------------------------------------------
        # 1) Safety gate (placeholder: true unless later modules veto)
        # ------------------------------------------------------------
        safety_ok = True

        # ------------------------------------------------------------
        # 2) Volatility gate (placeholder using vol_norm)
        # ------------------------------------------------------------
        # If vol_norm is missing early, we block (conservative).
        if feats.vol_norm is None:
            volatility_ok = False
            vol_reason = "VOLGATE:vol_norm_missing"
        else:
            volatility_ok = (self.cfg.vol_norm_min <= feats.vol_norm <= self.cfg.vol_norm_max)
            vol_reason = f"VOLGATE:vol_norm={feats.vol_norm:.3f}"

        # ------------------------------------------------------------
        # 3) Regime (placeholder)
        # ------------------------------------------------------------
        # If we don’t have enough signal yet, return UNKNOWN + BLOCK.
        # Later: HMM / direction gate will set TREND vs MEAN_REVERSION.
        if feats.velocity is None:
            # conservative: unknown until velocity exists
            regime = MarketRegime.UNKNOWN
            confidence = 0.0
            permission = TradePermission.BLOCK
            reason = f"REGIME:unknown_velocity_missing|{vol_reason}"
            return default_unknown_state(ts, instrument, reason)

        # Simple placeholder regime logic:
        # - positive velocity -> TREND
        # - near zero / negative -> MEAN_REVERSION (placeholder)
        if feats.velocity > 0:
            regime = MarketRegime.TREND
        else:
            regime = MarketRegime.MEAN_REVERSION

        # ------------------------------------------------------------
        # 4) Permission decision (gates first, then confidence)
        # ------------------------------------------------------------
        confidence = self.cfg.base_confidence
        reason = f"REGIME:{regime.value}|{vol_reason}"

        if not safety_ok:
            permission = TradePermission.BLOCK
            reason = f"SAFETY:block|{reason}"
        elif not volatility_ok:
            permission = TradePermission.BLOCK
            reason = f"VOL:block|{reason}"
        else:
            permission = TradePermission.PERMIT

        return MarketState(
            timestamp=ts,
            instrument=instrument,
            regime=regime,
            permission=permission,
            safety_ok=safety_ok,
            volatility_ok=volatility_ok,
            early_exit_active=False,
            confidence=confidence,
            reason=reason,
        )