import pytest

pytest.importorskip("pydantic")

from datetime import date, timedelta

from app.domain.models import SchemaFollowUp
from app.services.tracking import followup_kpis


def test_followup_kpis_overdue():
    items = [
        SchemaFollowUp(schema_name="A", owner="Juan", due_date=date.today() - timedelta(days=1), status="Pendiente"),
        SchemaFollowUp(schema_name="B", owner="", due_date=None, status="Pendiente"),
    ]
    kpis = followup_kpis(items)
    assert kpis["total"] == 2
    assert kpis["overdue"] == 1
    assert kpis["with_owner"] == 1
