import pytest

pytest.importorskip("pydantic")

from app.config.settings import load_rules_config
from app.domain.models import Classification, SchemaSummary
from app.rules.evaluator import RuleEngine


def test_archive_candidate_or_ready():
    engine = RuleEngine(load_rules_config())
    schema = SchemaSummary(
        schema_name="ARCHIVE",
        last_login_days_ago=700,
        active_jobs=0,
        apex_applications=0,
        external_dependencies=0,
        enabled_triggers=0,
        account_status="LOCKED",
        recent_activity=False,
    )
    result = engine.evaluate(schema)
    assert result.classification in {Classification.PROBABLE_CANDIDATE, Classification.READY_PRE_CLEANUP}


def test_active_schema_blocked_activity():
    engine = RuleEngine(load_rules_config())
    schema = SchemaSummary(
        schema_name="ACTIVE_APP",
        last_login_days_ago=10,
        active_jobs=2,
        apex_applications=1,
        external_dependencies=0,
        enabled_triggers=1,
        recent_activity=True,
    )
    result = engine.evaluate(schema)
    assert result.classification == Classification.BLOCKED_ACTIVITY
