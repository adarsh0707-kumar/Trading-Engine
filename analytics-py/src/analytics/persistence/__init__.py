"""Persistence abstractions for the analytics service.

This package contains database-agnostic repository contracts.
Concrete persistence implementations belong in infrastructure-specific
modules and must not leak database concerns into the analytics domain.
"""
