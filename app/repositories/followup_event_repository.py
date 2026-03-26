from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domain.models import FollowUpEvent


class FollowUpEventRepository:
    def __init__(self, path: str = "app/data/followup_events.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_all(self) -> list[FollowUpEvent]:
        if not self.path.exists():
            return []
        df = pd.read_csv(self.path)
        return [FollowUpEvent(**row) for row in df.to_dict(orient="records")]

    def add_event(self, event: FollowUpEvent) -> None:
        rows = [e.model_dump() for e in self.list_all()]
        rows.append(event.model_dump())
        pd.DataFrame(rows).to_csv(self.path, index=False)

    def list_for_schema(self, schema_name: str) -> list[FollowUpEvent]:
        return [e for e in self.list_all() if e.schema_name == schema_name]
