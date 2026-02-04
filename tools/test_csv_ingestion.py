from feeds.market_feed import MarketFeed 

import yaml

with open("config/orchestrator.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

feed = MarketFeed(config)

count = 0
for features in feed.stream():
    print(features)
    count += 1
    if count >= 5:
        break

print(f"\nOK - read {count} MarketFeatures rows.")