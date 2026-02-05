from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Signal:
    timestamp: datetime
    instrument: str

    strategy: str               # "SystemA" | "SystemB"
    action: str                 # "ENTER_LONG" | "ENTER_SHORT" | "EXIT" | "HOLD"
    strength: float             # 0..1

    reason: str
    tag: Optional[str] = None   # free-form: "breakout", "mr_pullback", etc.