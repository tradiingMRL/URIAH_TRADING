from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------
# Market data event
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MarketEvent:
    timestamp: datetime
    instrument: str
    price: float
    volume: float

# ---------------------------------------------------------------------
# Strategy / router signal
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class SignalEvent:
    timestamp: datetime
    instrument: str
    strategy: str
    action: str        # BUY | SELL | HOLD
    strength: float
    reason: str
    tag: Optional[str] = None