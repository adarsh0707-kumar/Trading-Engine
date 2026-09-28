"""Persistence-layer application errors."""

from __future__ import annotations


class PersistenceError(RuntimeError):
    """Raised when persistence of processed analytics data fails."""


__all__ = ["PersistenceError"]
