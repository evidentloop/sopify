"""The writer for Sopify protocol state and receipts.

Public surface: iso_now for timestamp generation.
StateStore (sopify_writer.store) writes P8 protocol state files
(active_plan.json, current_handoff.json).

Dependency direction: sopify_writer → sopify_contracts (one-way).
"""

from ._time import iso_now

__all__ = [
    "iso_now",
]
