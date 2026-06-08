"""The writer for Sopify protocol state and receipts.

Public surface: iso_now for timestamp generation.
StateStore remains in sopify_writer.store as a temporary internal implementation
for runtime/ modules; it writes retired runtime state files and is NOT part of the
post-P8 public writer API. It will be removed when runtime/ is deleted (W2.10).

Dependency direction: sopify_writer → sopify_contracts (one-way).
"""

from ._time import iso_now

__all__ = [
    "iso_now",
]
