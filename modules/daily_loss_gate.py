from dataclasses import dataclass


@dataclass(frozen=True)
class DailyLossDecision:
    ok: bool
    reason: str


class DailyLossGate:
    """
    Daily loss limit (e.g., 3%) - STUB.

    Later: compute daily realised drawdown from trade events / equity curve.
    For now:
      - enabled false => OK
      - enabled true + force_block true => FAIL (block new entries)
    """

    def __init__(self, config: dict):
        cfg = config or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.limit_frac = float(cfg.get("limit_frac", 0.03))  # placeholder for later
        self.force_block = bool(cfg.get("force_block", False))
        self.force_reason = str(cfg.get("force_reason", "manual_daily_loss_block"))

    def check(self) -> DailyLossDecision:
        if not self.enabled:
            return DailyLossDecision(True, "daily_loss_disabled_stub")

        if self.force_block:
            return DailyLossDecision(False, self.force_reason)

        return DailyLossDecision(True, "daily_loss_ok_stub")