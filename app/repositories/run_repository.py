from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.domain.models import AnalysisRun, SchemaEvaluation


class RunRepository:
    def __init__(self, base_dir: str = "app/data/runs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run: AnalysisRun) -> Path:
        out = self.base_dir / f"{run.run_id}.json"
        out.write_text(run.model_dump_json(indent=2), encoding="utf-8")
        return out

    def load(self, run_id: str) -> AnalysisRun:
        data = json.loads((self.base_dir / f"{run_id}.json").read_text(encoding="utf-8"))
        return AnalysisRun.model_validate(data)

    def list_runs(self) -> list[str]:
        return sorted([p.stem for p in self.base_dir.glob("*.json")])

    def to_dataframe(self, run: AnalysisRun) -> pd.DataFrame:
        return pd.DataFrame([e.model_dump() for e in run.evaluations])


def build_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


def compare_runs(old: AnalysisRun, new: AnalysisRun) -> pd.DataFrame:
    old_map: dict[str, SchemaEvaluation] = {e.schema_name: e for e in old.evaluations}
    rows = []
    for e in new.evaluations:
        prev = old_map.get(e.schema_name)
        rows.append(
            {
                "schema_name": e.schema_name,
                "old_classification": prev.classification.value if prev else "N/A",
                "new_classification": e.classification.value,
                "old_risk": prev.risk_score if prev else None,
                "new_risk": e.risk_score,
                "delta_risk": e.risk_score - prev.risk_score if prev else None,
                "new_blocking": ", ".join(e.blocking_signals),
            }
        )
    return pd.DataFrame(rows)


def compare_runs_summary(old: AnalysisRun, new: AnalysisRun) -> dict[str, int]:
    cmp = compare_runs(old, new)
    if cmp.empty:
        return {
            "new_candidates": 0,
            "state_changes": 0,
            "risk_increase": 0,
            "risk_decrease": 0,
        }
    new_candidates = int((cmp["new_classification"] == "Candidato probable").sum())
    state_changes = int((cmp["old_classification"] != cmp["new_classification"]).sum())
    risk_increase = int(cmp["delta_risk"].fillna(0).gt(0).sum())
    risk_decrease = int(cmp["delta_risk"].fillna(0).lt(0).sum())
    return {
        "new_candidates": new_candidates,
        "state_changes": state_changes,
        "risk_increase": risk_increase,
        "risk_decrease": risk_decrease,
    }
