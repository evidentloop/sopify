"""The writer for Sopify protocol state and receipts.

Public surface:
  ProtocolStore — unified read/write for protocol state, receipts, and finalize.
  InvariantViolationError — raised when writes violate a protocol contract.
  iso_now — UTC timestamp generator.

Dependency direction: sopify_writer → sopify_contracts (one-way).
"""

from ._time import iso_now
from .invariants import InvariantViolationError
from .store import ProtocolStore

__all__ = [
    "ProtocolStore",
    "InvariantViolationError",
    "iso_now",
]
