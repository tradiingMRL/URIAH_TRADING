# io/sources/nt8_stream.py

from typing import Iterator
from contracts.messages import MarketFeatures


class NT8StreamSource:
    """
    Stub for NT8 → Python live feed.
    Implementation intentionally deferred.
    """

    def __init__(self, config: dict):
        self.config = config

    def stream(self) -> Iterator[MarketFeatures]:
        raise NotImplementedError(
            "NT8StreamSource not implemented. Use CSV replay mode."
        )