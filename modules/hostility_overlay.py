from dataclasses import dataclass
from enum import Enum
from typing import Optional

from contracts.messages import MarketFeatures


class HostilityState(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HOSTILE = "HOSTILE"


@dataclass(frozen=True)
class HostilityDecision:
    state: HostilityState
    allow_new_entries: bool
    reason: str

    # Optional future metrics (dashboard)
    lcr: float = 0.0
    dlcr: float = 0.0
    ddlcr: float = 0.0
    k_live: int = 0
    window_min: int = 0


class HostilityOverlay:
    """
    LAYER 0: Market Hostility Overlay v2 (STUB)

    - enabled: false => NORMAL
    - enabled: true + force_state => forced state
    - enabled: true + no force_state => NORMAL
    """

    def __init__(self, config: dict):
        cfg = config or {}
        self.enabled: bool = bool(cfg.get("enabled", False))

        # Stub controls
        self.force_state: Optional[str] = cfg.get("force_state", None)
        self.force_reason: str = str(cfg.get("force_reason", "forced_hostility"))

        # Future placeholders
        self.window_min: int = int(cfg.get("window_min", 30))

    def evaluate(self, features: MarketFeatures) -> HostilityDecision:
        if not self.enabled:
            return HostilityDecision(
                state=HostilityState.NORMAL,
                allow_new_entries=True,
                reason="hostility_disabled_stub",
                window_min=self.window_min,
            )

        if self.force_state:
            st = str(self.force_state).upper().strip()
            if st not in ("NORMAL", "ELEVATED", "HOSTILE"):
                st = "NORMAL"
            state = HostilityState(st)
            allow = state != HostilityState.HOSTILE
            return HostilityDecision(
                state=state,
                allow_new_entries=allow,
                reason=f"hostility_forced:{self.force_reason}",
                window_min=self.window_min,
            )

        return HostilityDecision(
            state=HostilityState.NORMAL,
            allow_new_entries=True,
            reason="hostility_enabled_stub_default_normal",
            window_min=self.window_min,
        )