import pytest

pytest.importorskip("pydantic")

from datetime import datetime, timezone

from app.domain.models import AnalysisRun, Classification, SchemaEvaluation, Severity
from app.repositories.run_repository import compare_runs_summary


def _ev(schema_name: str, classification: Classification, risk: int) -> SchemaEvaluation:
    return SchemaEvaluation(
        schema_name=schema_name,
        obsolescence_score=50,
        risk_score=risk,
        severity=Severity.MEDIUM,
        classification=classification,
        triggered_rules=[],
        blocking_signals=[],
        executive_summary="",
        technical_detail="",
        next_phase="Fase 1: Análisis inicial",
        decision="",
    )


def test_compare_runs_summary_basic():
    old = AnalysisRun(
        run_id="old",
        run_ts=datetime.now(timezone.utc),
        environment="INT",
        data_source="Mocks",
        rules_version="1",
        schema_count=1,
        evaluations=[_ev("A", Classification.UNDER_REVIEW, 40)],
    )
    new = AnalysisRun(
        run_id="new",
        run_ts=datetime.now(timezone.utc),
        environment="INT",
        data_source="Mocks",
        rules_version="1",
        schema_count=1,
        evaluations=[_ev("A", Classification.PROBABLE_CANDIDATE, 60)],
    )

    summary = compare_runs_summary(old, new)
    assert summary["state_changes"] == 1
    assert summary["new_candidates"] == 1
    assert summary["risk_increase"] == 1
