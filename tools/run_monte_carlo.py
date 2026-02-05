import argparse
import csv
import json
import os
from typing import List

from modules.monte_carlo_filter import MonteCarloConfig, run_monte_carlo, save_report


def _read_r_from_csv(path: str, r_col: str) -> List[float]:
    out: List[float] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or r_col not in reader.fieldnames:
            raise ValueError(f"CSV missing column '{r_col}'. Columns: {reader.fieldnames}")
        for row in reader:
            s = (row.get(r_col) or "").strip()
            if not s:
                continue
            out.append(float(s))
    return out


def _read_r_from_ndjson(path: str, r_key: str) -> List[float]:
    out: List[float] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if r_key in obj and obj[r_key] is not None:
                out.append(float(obj[r_key]))
    return out


def main() -> int:
    p = argparse.ArgumentParser()

    p.add_argument("--input", required=True, help="Path to CSV or NDJSON file containing R multiples")
    p.add_argument("--format", choices=["csv", "ndjson"], default=None, help="If omitted, inferred from extension")
    p.add_argument("--r-col", default="R", help="CSV column name holding R multiples (default: R)")
    p.add_argument("--r-key", default="R", help="NDJSON key holding R multiples (default: R)")
    p.add_argument("--out", default=r".\out\risk_report.json", help="Output report path")

    # MC params
    p.add_argument("--paths", type=int, default=10000)
    p.add_argument("--horizon", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)

    # slippage model in R
    p.add_argument("--slip-mean", type=float, default=0.0)
    p.add_argument("--slip-std", type=float, default=0.0)

    # Option A: loss-budget gate
    p.add_argument("--budget-r", type=float, default=7.0, help="Loss budget in R over horizon (peak-to-trough DD in cum R)")
    p.add_argument("--p-budget", type=float, default=0.10, help="BLOCK if P(DD_R >= budget) > this")

    # streak definition for dashboard (counts scratches as loss by default)
    p.add_argument("--loss-leq-zero", action="store_true", help="Count R<=0 as loss (default)")
    p.add_argument("--loss-lt-zero", action="store_true", help="Count only R<0 as loss")

    # minimum trades required
    p.add_argument("--min-trades", type=int, default=30)

    args = p.parse_args()

    fmt = args.format
    if fmt is None:
        ext = os.path.splitext(args.input)[1].lower()
        fmt = "ndjson" if ext in [".ndjson", ".jsonl"] else "csv"

    if fmt == "csv":
        r = _read_r_from_csv(args.input, args.r_col)
    else:
        r = _read_r_from_ndjson(args.input, args.r_key)

    # loss definition
    loss_is_leq_zero = True
    if args.loss_lt_zero:
        loss_is_leq_zero = False
    if args.loss_leq_zero:
        loss_is_leq_zero = True

    cfg = MonteCarloConfig(
        n_paths=args.paths,
        horizon_trades=args.horizon,
        seed=args.seed,
        slippage_r_mean=args.slip_mean,
        slippage_r_std=args.slip_std,
        loss_budget_r=args.budget_r,
        prob_loss_budget_exceed_threshold=args.p_budget,
        loss_is_r_leq_zero=loss_is_leq_zero,
        min_trades_required=args.min_trades,
    )

    result = run_monte_carlo(r, cfg)
    save_report(result, args.out)

    print(f"Wrote: {args.out}")
    print(f"financial_ok={result.financial_ok} reason={result.reason}")

    # Option A gate stats
    if not (result.prob_dd_r_ge_budget != result.prob_dd_r_ge_budget):  # not NaN
        print(f"P(DD_R >= {result.loss_budget_r:.2f}R) = {result.prob_dd_r_ge_budget:.4f}  (block if > {cfg.prob_loss_budget_exceed_threshold:.2f})")
        print(f"DD_R p95={result.dd_r_p95:.4f}  p99={result.dd_r_p99:.4f}")

    # Dashboard line: “MC predicts X losing streak”
    if not (result.max_ls_p95 != result.max_ls_p95):  # not NaN
        print(f"MC predicts max losing streak (p95) ≈ {result.max_ls_p95:.0f} over next {result.horizon_trades} trades")
        print(f"max losing streak p99≈{result.max_ls_p99:.0f} | loss_rate≈{result.loss_rate:.2%} | avg_loss≈{result.avg_loss_r_mag:.3f}R")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())