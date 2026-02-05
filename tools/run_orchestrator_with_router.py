import time
import datetime

from orchestrator.orchestrator import Orchestrator
from router.strategy_router import StrategyRouter
from contracts.messages import MarketFeatures


def main():
    # -----------------------------
    # Initialise orchestrator + router
    # -----------------------------
    config = {
        "monte_carlo": {
            "baseline_path": r".\out\risk_report_baseline.json",
            "recent_path": r".\out\risk_report_recent.json",
            "drift_threshold": 0.05,
        }
    }

    orch = Orchestrator(config)
    router = StrategyRouter(config)

    # -----------------------------
    # Synthetic price stream
    # -----------------------------
    price = 5000.0
    i = 0

    print("Starting orchestrator runner...\n")

    while True:
        # ---------------------------------
        # Create a simple synthetic regime
        # ---------------------------------
        step = i % 60

        # Phase A: trend (build history)
        if step < 20:
            price += 0.25

        # Phase B: chop / consolidation
        elif step < 40:
            price = 5020.0 + (step % 2) * 0.25

        # Phase C: breakout attempt
        else:
            price = 5040.0

        # ---------------------------------
        # Build market features
        # ---------------------------------
        features = MarketFeatures(
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            instrument="MES",
            price=price,
            volume=1000.0,
            atr_fast=1.0,
            atr_slow=2.0,
            vol_norm=0.5,
            velocity=0.1,
        )

        # ---------------------------------
        # Orchestrator → MarketState
        # ---------------------------------
        state = orch.step(features)

        # PRINT STATE (THIS IS IMPORTANT)
        print(
            f"i={i} step={step} price={price:.2f} "
            f"regime={state.regime} permission={state.permission}"
        )
        print("STATE_REASON:", state.reason)

        # ---------------------------------
        # Router → Signal
        # ---------------------------------
        signal = router.route(features, state)
        print(signal)
        print("-" * 80)

        # ---------------------------------
        # Loop
        # ---------------------------------
        i += 1
        time.sleep(1)


if __name__ == "__main__":
    main()