"""Backward-compatible import for the canonical score component."""

from models.score_component import ScoreComponent

SignalResult = ScoreComponent

__all__ = ["SignalResult"]
