import os
from typing import Optional, Tuple

from contracts.enums import TradePermission
from modules.monte_carlo_filter import load_report


def mc_veto(report_path: str = r".\out\risk_report.json") -> Tuple[TradePermission, str]:
    """
    Reads the most recent Monte Carlo risk report and returns:
      (TradePermission.ALLOW/BLOCK, reason)

    Policy:
      - If no report exists => ALLOW but mark reason (dev mode)
      - If report exists and financial_ok is False => BLOCK
      - If report exists and financial_ok is True => ALLOW
    """
    report = load_report(report_path)
    if report is None:
        return (TradePermission.ALLOW, f"MC:no_report:{report_path}")

    ok = bool(report.get("financial_ok", False))
    reason = str(report.get("reason", "mc_unknown"))

    if not ok:
        return (TradePermission.BLOCK, f"MC_FAIL:{reason}")

    return (TradePermission.ALLOW, f"MC_OK:{reason}")