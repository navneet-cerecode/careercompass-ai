"""Backward-compatible import for the canonical match assessment."""

from models.match_assessment import MatchAssessment

MatchResult = MatchAssessment

__all__ = ["MatchResult"]
