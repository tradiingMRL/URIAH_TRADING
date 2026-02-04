from dataclasses import dataclass
from datetime import datetime

from contracts.enums import MarketRegime, TradePermission


@dataclass(frozen=True)
class MarketState:
    timestamp: datetime
    instrument: str

    regime: MarketRegime
    permission: TradePermission

    safety_ok: bool
    volatility_ok: bool
    early_exit_active: bool

    confidence: float
    reason: str