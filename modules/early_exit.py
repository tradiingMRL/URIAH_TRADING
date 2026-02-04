from dataclasses import dataclass
from contracts.messages import MarketFeatures


@dataclass(frozen=True)
class EarlyExitDecision:
    active: bool
    permission: str   # "ALLOW" | "REDUCE" | "BLOCK"
    reason: str


class EarlyExit:
    """
    Early Exit (stub v1):
    - Permission can only be downgraded.
    - Controlled by config for plumbing proof.
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.force_active = bool(self.config.get("force_active", False))
        self.force_permission = str(self.config.get("force_permission", "REDUCE")).upper()
        self.force_reason = str(self.config.get("force_reason", "early_exit_forced"))

        if self.force_permission not in ("ALLOW", "REDUCE", "BLOCK"):
            raise ValueError("early_exit.force_permission must be ALLOW|REDUCE|BLOCK")

    def check(self, features: MarketFeatures) -> EarlyExitDecision:
        if not self.force_active:
            return EarlyExitDecision(False, "ALLOW", "early_exit_inactive")

        return EarlyExitDecision(True, self.force_permission, self.force_reason)