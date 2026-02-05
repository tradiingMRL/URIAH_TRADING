import yaml

from feeds.market_feed import MarketFeed
from orchestrator.orchestrator import Orchestrator
from router.strategy_router import StrategyRouter


def main():
    with open("config/orchestrator.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    feed = MarketFeed(config)
    orch = Orchestrator(config)
    router = StrategyRouter(config)

    n = 0
    for features in feed.stream():
        state = orch.step(features)
        sig = router.route(features, state)
        print("FEATURES", features) 

        print(state)
        print(sig)
        print("-" * 80)

        n += 1
        if n >= 10:
            break

    print(f"\nOK - routed {n} ticks.")


if __name__ == "__main__":
    main()