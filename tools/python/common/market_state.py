from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------
# Core enums (keep these stable — many modules will depend on them)
# ---------------------------------------------------------------------

class MarketRegime(str, Enum):
    HALT = "HALT"                 # do nothing (outside session, bad data, etc.)
    TREND = "TREND"               # trending conditions
    MEAN_REVERSION = "MEAN_REVERSION"
    CHOP = "CHOP"                 # noisy / low edge / indecision
    UNKNOWN = "UNKNOWN"           # fallback until enough data


class TradePermission(str, Enum):
    BLOCK = "BLOCK"               # hard veto: no new trades
    PERMIT = "PERMIT"             # trades allowed
    REDUCE = "REDUCE"             # allow but reduce risk / be conservative


# ---------------------------------------------------------------------
# Feature snapshot (minimal, extend as needed)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MarketFeatures:
    timestamp: datetime
    instrument: str
    price: float
    volume: float

    # Core risk / volatility descriptors (can be None early)
    atr_fast: Optional[float] = None
    atr_slow: Optional[float] = None

    # Non-ATR volatility gate inputs (placeholders for your custom measure)
    vol_norm: Optional[float] = None
    velocity: Optional[float] = None


# ---------------------------------------------------------------------
# Decision-state snapshot (output of the gating + regime logic)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MarketState:
    timestamp: datetime
    instrument: str

    regime: MarketRegime
    permission: TradePermission

    # safety + governance gates
    safety_ok: bool
    volatility_ok: bool

    # risk management switches
    early_exit_active: bool = False

    # confidence & traceability
    confidence: float = 0.0
    reason: str = ""


# ---------------------------------------------------------------------
# Helper constructors (clean defaults)
# ---------------------------------------------------------------------

def default_halt_state(ts: datetime, instrument: str, reason: str) -> MarketState:
    return MarketState(
        timestamp=ts,
        instrument=instrument,
        regime=MarketRegime.HALT,
        permission=TradePermission.BLOCK,
        safety_ok=False,
        volatility_ok=False,
        early_exit_active=False,
        confidence=0.0,
        reason=reason,
    )


def default_unknown_state(ts: datetime, instrument: str, reason: str) -> MarketState:
    return MarketState(
        timestamp=ts,
        instrument=instrument,
        regime=MarketRegime.UNKNOWN,
        permission=TradePermission.BLOCK,
        safety_ok=True,
        volatility_ok=False,
        early_exit_active=False,
        confidence=0.0,
        reason=reason,
    )