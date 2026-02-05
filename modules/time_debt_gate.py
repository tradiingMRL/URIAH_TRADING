from dataclasses import dataclass


@dataclass(frozen=True)
class TimeDebtDecision:
    ok: bool
    permission: str  # "ALLOW" | "BLOCK"
    reason: str


class TimeDebtGate:
    """
    Time Debt Gate - STUB (ALLOW/BLOCK only).

    Purpose: governance filter that can PAUSE new entries when "time debt" is high.
    This gate does NOT do position sizing. It only returns:
      - ALLOW: normal operation
      - BLOCK: no new entries (router veto)

    Current stub supports force tests via config:
      time_debt:
        enabled: true
        force_permission: "BLOCK"   # "ALLOW" or "BLOCK"
        force_reason: "manual_time_debt_block_test"
    """

    def __init__(self, config: dict):
        cfg = config or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.force_permission = str(cfg.get("force_permission", "ALLOW")).upper()
        self.force_reason = str(cfg.get("force_reason", "time_debt_stub"))

        if self.force_permission not in ("ALLOW", "BLOCK"):
            # fail-closed: invalid config blocks
            self.force_permission = "BLOCK"
            self.force_reason = "invalid_time_debt_force_permission"

    def check(self) -> TimeDebtDecision:
        if not self.enabled:
            return TimeDebtDecision(ok=True, permission="ALLOW", reason="time_debt_disabled")

        # stub: forced permission
        if self.force_permission == "BLOCK":
            return TimeDebtDecision(ok=False, permission="BLOCK", reason=f"time_debt_forced:{self.force_reason}")

        return TimeDebtDecision(ok=True, permission="ALLOW", reason=f"time_debt_forced:{self.force_reason}")