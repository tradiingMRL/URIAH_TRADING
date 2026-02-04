# utils/exceptions.py

class ContractError(Exception):
    """
    Raised when inbound data violates the MarketFeatures contract.
    These are fatal for the current run.
    """
    pass


class DataQualityError(Exception):
    """
    Raised when data is malformed but structurally valid.
    The system may choose to skip or halt depending on policy.
    """
    pass