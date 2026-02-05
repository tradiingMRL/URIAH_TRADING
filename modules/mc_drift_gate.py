from dataclasses import dataclass
from typing import Optional, Tuple

from contracts.enums import TradePermission
from modules.monte_carlo_filter import load_report


@dataclass
class DriftDecision:
    permission: TradePermission
    reason: str


def _get_float(d: dict, key: str) -> Optional[float]:
    try:
        v = d.get(key, None)
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def mc_drift_veto(
    baseline_path: str = r".\out\risk_report_baseline.json",
    recent_path: str = r".\out\risk_report_recent.json",
    drift_threshold: float = 0.05,
) -> Tuple[TradePermission, str]:
    """
    Binary MC veto using:
      1) Absolute recent MC decision (financial_ok)
      2) Drift in tail risk: (p_recent - p_baseline) > drift_threshold => BLOCK

    Inputs are MC reports produced by tools/run_monte_carlo.py from Option A engine.

    Policy:
      - If recent report missing => BLOCK (fail-closed; no trading without current risk assessment)
      - If recent report says financial_ok False => BLOCK
      - If baseline missing => ALLOW (drift disabled) but annotate reason
      - Else compute drift on prob_dd_r_ge_budget and BLOCK if drift exceeds threshold
    """
    recent = load_report(recent_path)
    if recent is None:
        return (TradePermission.BLOCK, f"MC_FAIL:no_recent_report:{recent_path}")

    recent_ok = bool(recent.get("financial_ok", False))
    recent_reason = str(recent.get("reason", "mc_unknown"))
    p_recent = _get_float(recent, "prob_dd_r_ge_budget")

    if not recent_ok:
        # Absolute gate fail already
        return (TradePermission.BLOCK, f"MC_FAIL:{recent_reason}")

    baseline = load_report(baseline_path)
    if baseline is None:
        # Drift cannot be computed yet; allow but mark it
        return (TradePermission.ALLOW, f"MC_OK:{recent_reason}|MC_DRIFT:no_baseline:{baseline_path}")

    p_base = _get_float(baseline, "prob_dd_r_ge_budget")
    base_reason = str(baseline.get("reason", "mc_unknown"))

    if p_recent is None or p_base is None:
        # Missing probability fields: allow but annotate (you'll fix once real logs exist)
        return (
            TradePermission.ALLOW,
            f"MC_OK:{recent_reason}|MC_DRIFT:missing_p_fields:recent={p_recent}_base={p_base}",
        )

    drift = p_recent - p_base

    if drift > float(drift_threshold):
        return (
            TradePermission.BLOCK,
            f"MC_FAIL_DRIFT:dp={drift:.3f}_gt_{float(drift_threshold):.3f}|p_recent={p_recent:.3f}|p_base={p_base:.3f}",
        )

    return (
        TradePermission.ALLOW,
        f"MC_OK:{recent_reason}|MC_DRIFT_OK:dp={drift:.3f}_le_{float(drift_threshold):.3f}|p_recent={p_recent:.3f}|p_base={p_base:.3f}",
    )