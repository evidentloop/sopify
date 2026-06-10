"""Domain-level validators for Sopify protocol state writes."""


class InvariantViolationError(ValueError):
    """Raised when state writes violate a protocol contract."""
