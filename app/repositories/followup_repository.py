from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domain.models import SchemaFollowUp


class FollowUpRepository:
    def __init__(self, path: str = "app/data/followup.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[SchemaFollowUp]:
        if not self.path.exists():
            return []
        df = pd.read_csv(self.path)
        return [SchemaFollowUp(**row) for row in df.to_dict(orient="records")]

    def save(self, items: list[SchemaFollowUp]) -> None:
        pd.DataFrame([i.model_dump() for i in items]).to_csv(self.path, index=False)
