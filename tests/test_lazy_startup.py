import importlib
import sys


def test_career_compass_does_not_import_external_clients_at_startup():
    sys.modules.pop("core.career_compass", None)
    sys.modules.pop("services.llm.evaluator", None)
    sys.modules.pop("services.recommendation.recommendation_engine", None)

    career_compass = importlib.import_module("core.career_compass")
    compass = career_compass.CareerCompass()

    assert "evaluator" not in compass.__dict__
    assert "recommendation_engine" not in compass.__dict__
    assert "recommendation_service" not in compass.__dict__
    assert "services.llm.evaluator" not in sys.modules
    assert "services.recommendation.recommendation_engine" not in sys.modules


def test_graph_build_does_not_construct_job_provider(monkeypatch):
    from graph import nodes
    from graph.workflow import build_workflow

    nodes.get_job_agent.cache_clear()

    class UnexpectedJobAgent:
        def __init__(self):
            raise AssertionError("Job provider was constructed while building the graph")

    monkeypatch.setattr(nodes, "JobDiscoveryAgent", UnexpectedJobAgent)

    workflow = build_workflow()

    assert workflow is not None
    assert nodes.get_job_agent.cache_info().currsize == 0
