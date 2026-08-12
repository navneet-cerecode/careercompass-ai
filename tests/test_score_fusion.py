from models.score_component import ScoreComponent
from services.recommendation.fusion import ScoreFusion


def test_score_fusion_applies_current_signal_weights():
    signals = [
        ScoreComponent(
            name="Skill Signal",
            score=80,
            explanation="Matched four of five skills.",
        ),
        ScoreComponent(
            name="Semantic Signal",
            score=50,
            explanation="Moderate semantic similarity.",
        ),
    ]

    assert ScoreFusion().combine(signals) == 62.0


def test_score_fusion_returns_zero_without_signals():
    assert ScoreFusion().combine([]) == 0.0


def test_score_fusion_excludes_signals_without_evidence():
    signals = [
        ScoreComponent(
            name="Skill Signal",
            score=50,
            evidence_available=False,
        ),
        ScoreComponent(name="Semantic Signal", score=72),
    ]

    fusion = ScoreFusion()

    assert fusion.combine(signals) == 72
    assert fusion.evidence_coverage(signals) == 0.6
