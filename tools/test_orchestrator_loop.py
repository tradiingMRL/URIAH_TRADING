import yaml

from feeds.market_feed import MarketFeed
from orchestrator.orchestrator import Orchestrator


def main():
    with open("config/orchestrator.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    feed = MarketFeed(config)
    orch = Orchestrator(config)

    n = 0
    for features in feed.stream():
        state = orch.step(features)
        print(state)
        n += 1
        if n >= 5:
            break

    print(f"\nOK - emitted {n} MarketState rows.")


if __name__ == "__main__":
    main()