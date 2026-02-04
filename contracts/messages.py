# contracts/messages.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketFeatures:
    """
    Canonical inbound feature contract.

    All timestamps MUST be UTC and timezone-aware.
    """
    timestamp: datetime
    instrument: str

    price: float
    volume: float

    atr_fast: float
    atr_slow: float
    vol_norm: float
    velocity: float