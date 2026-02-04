from typing import Iterator

from contracts.messages import MarketFeatures
from feeds.sources.csv_replay import stream_csv_replay
from feeds.sources.nt8_stream import NT8StreamSource


class MarketFeed:
    """
    Routes inbound market data from the configured source.
    """

    def __init__(self, config: dict):
        self.config = config

    def stream(self) -> Iterator[MarketFeatures]:
        mode = self.config.get("feed_mode", "csv_replay")

        if mode == "csv_replay":
            cfg = self.config["csv_replay"]
            yield from stream_csv_replay(
                path=cfg["path"],
                max_rows=cfg.get("max_rows"),
            )
            return

        if mode == "nt8_live":
            src = NT8StreamSource(self.config["nt8_live"])
            yield from src.stream()
            return

        raise ValueError(f"Unknown feed_mode: {mode}")