import json
import math
import os
import random
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple


@dataclass
class MonteCarloConfig:
    # Monte Carlo parameters
    n_paths: int = 10_000
    horizon_trades: int = 100
    seed: int = 42

    # --- R-stream slippage model (applied additively to each trade's R) ---
    slippage_r_mean: float = 0.0
    slippage_r_std: float = 0.0
    slippage_r_clip: float = 2.0  # caps extreme noise

    # --- Option A: Loss-budget gate (binary) ---
    # Budget is in R units (peak-to-trough drawdown in cumulative R over horizon)
    loss_budget_r: float = 7.0
    prob_loss_budget_exceed_threshold: float = 0.10  # BLOCK if P(DD_R >= budget) > this

    # --- Dashboard: losing streak projection (not a gate by itself, but reported) ---
    # Treat scratch as loss? For chop detection, default is <= 0 (counts scratch)
    loss_is_r_leq_zero: bool = True

    # Minimum trades needed to run MC safely
    min_trades_required: int = 30


@dataclass
class MonteCarloResult:
    n_paths: int
    horizon_trades: int
    n_trades_in_sample: int

    # --- Loss budget metrics (Option A gate) ---
    loss_budget_r: float
    prob_dd_r_ge_budget: float

    dd_r_mean: float
    dd_r_p50: float
    dd_r_p95: float
    dd_r_p99: float

    # --- Losing streak projection metrics (for dashboard) ---
    max_ls_mean: float
    max_ls_p50: float
    max_ls_p95: float
    max_ls_p99: float

    # --- Sample diagnostics (helps explain “getting worse”) ---
    avg_loss_r_mag: float     # average magnitude of losing trades in the input stream
    loss_rate: float          # fraction of trades counted as losses by the chosen definition

    # --- Gate decision ---
    financial_ok: bool
    reason: str


def _percentile(xs: List[float], q: float) -> float:
    if not xs:
        return float("nan")
    xs_sorted = sorted(xs)
    idx = int(round(q * (len(xs_sorted) - 1)))
    idx = max(0, min(idx, len(xs_sorted) - 1))
    return xs_sorted[idx]


def _apply_slippage_r(r: float, cfg: MonteCarloConfig, rng: random.Random) -> float:
    if cfg.slippage_r_std <= 0.0 and cfg.slippage_r_mean == 0.0:
        return r
    z = rng.gauss(cfg.slippage_r_mean, cfg.slippage_r_std)
    z = max(-cfg.slippage_r_clip, min(cfg.slippage_r_clip, z))
    return r + z


def _max_losing_streak(rs: List[float], cfg: MonteCarloConfig) -> int:
    max_streak = 0
    cur = 0
    for r in rs:
        is_loss = (r <= 0.0) if cfg.loss_is_r_leq_zero else (r < 0.0)
        if is_loss:
            cur += 1
            if cur > max_streak:
                max_streak = cur
        else:
            cur = 0
    return max_streak


def _max_drawdown_in_cum_r(rs: List[float]) -> float:
    """
    Compute max peak-to-trough drawdown on cumulative R curve.
    Returns DD in R units (positive number).
    """
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in rs:
        cum += r
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    return max_dd


def run_monte_carlo(r_multiples: List[float], cfg: Optional[MonteCarloConfig] = None) -> MonteCarloResult:
    if cfg is None:
        cfg = MonteCarloConfig()

    # Clean input
    r_stream = []
    for r in r_multiples:
        if r is None:
            continue
        fr = float(r)
        if math.isnan(fr):
            continue
        r_stream.append(fr)

    n = len(r_stream)
    if n < cfg.min_trades_required:
        return MonteCarloResult(
            n_paths=0,
            horizon_trades=cfg.horizon_trades,
            n_trades_in_sample=n,
            loss_budget_r=cfg.loss_budget_r,
            prob_dd_r_ge_budget=float("nan"),
            dd_r_mean=float("nan"),
            dd_r_p50=float("nan"),
            dd_r_p95=float("nan"),
            dd_r_p99=float("nan"),
            max_ls_mean=float("nan"),
            max_ls_p50=float("nan"),
            max_ls_p95=float("nan"),
            max_ls_p99=float("nan"),
            avg_loss_r_mag=float("nan"),
            loss_rate=float("nan"),
            financial_ok=False,
            reason=f"insufficient_trades_for_mc_need>={cfg.min_trades_required}_have={n}",
        )

    # Diagnostics from sample
    losses = [r for r in r_stream if ((r <= 0.0) if cfg.loss_is_r_leq_zero else (r < 0.0))]
    avg_loss_r_mag = float("nan")
    if losses:
        avg_loss_r_mag = sum(abs(r) for r in losses) / len(losses)
    loss_rate = len(losses) / n

    rng = random.Random(cfg.seed)

    dd_rs: List[float] = []
    max_lss: List[int] = []
    budget_hits = 0

    for _ in range(cfg.n_paths):
        # Build one projected path of length H (bootstrap with replacement)
        path_rs: List[float] = []
        for _t in range(cfg.horizon_trades):
            r = r_stream[rng.randrange(0, n)]
            r = _apply_slippage_r(r, cfg, rng)
            path_rs.append(r)

        dd_r = _max_drawdown_in_cum_r(path_rs)
        ls = _max_losing_streak(path_rs, cfg)

        dd_rs.append(dd_r)
        max_lss.append(ls)

        if dd_r >= cfg.loss_budget_r:
            budget_hits += 1

    prob_budget = budget_hits / len(dd_rs)

    # Binary gate (Option A)
    financial_ok = prob_budget <= cfg.prob_loss_budget_exceed_threshold
    reason = "mc_pass" if financial_ok else f"mc_fail_prob_ddR_ge_{cfg.loss_budget_r:.2f}={prob_budget:.3f}_gt_{cfg.prob_loss_budget_exceed_threshold:.2f}"

    return MonteCarloResult(
        n_paths=cfg.n_paths,
        horizon_trades=cfg.horizon_trades,
        n_trades_in_sample=n,
        loss_budget_r=cfg.loss_budget_r,
        prob_dd_r_ge_budget=prob_budget,
        dd_r_mean=sum(dd_rs) / len(dd_rs),
        dd_r_p50=_percentile(dd_rs, 0.50),
        dd_r_p95=_percentile(dd_rs, 0.95),
        dd_r_p99=_percentile(dd_rs, 0.99),
        max_ls_mean=sum(max_lss) / len(max_lss),
        max_ls_p50=_percentile([float(x) for x in max_lss], 0.50),
        max_ls_p95=_percentile([float(x) for x in max_lss], 0.95),
        max_ls_p99=_percentile([float(x) for x in max_lss], 0.99),
        avg_loss_r_mag=avg_loss_r_mag,
        loss_rate=loss_rate,
        financial_ok=financial_ok,
        reason=reason,
    )


def save_report(result: MonteCarloResult, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, sort_keys=True)


def load_report(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)