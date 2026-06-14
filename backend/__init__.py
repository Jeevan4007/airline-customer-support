"""Airline Customer Support backend package.

Re-exports the main orchestrator so callers can simply do::

    from backend import airline_support_pipeline_safe
"""

from backend.pipeline import airline_support_pipeline_safe

__all__ = ["airline_support_pipeline_safe"]
