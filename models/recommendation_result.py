"""Backward-compatible import for the canonical match assessment."""

from models.match_assessment import MatchAssessment

RecommendationResult = MatchAssessment

__all__ = ["RecommendationResult"]
