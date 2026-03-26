from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domain.models import SchemaFollowUp, SchemaSummary


REQUIRED_COLUMNS = {
    "schema_name",
    "environment",
    "batch",
    "manager",
    "application",
    "size_gb",
    "object_count",
    "last_login_days_ago",
    "account_status",
    "active_jobs",
    "apex_applications",
    "external_dependencies",
    "enabled_triggers",
    "recent_activity",
}


def load_schema_summary_from_excel(path: str | Path, sheet_name: str = "schema_summary") -> list[SchemaSummary]:
    df = pd.read_excel(path, sheet_name=sheet_name)
    return _normalize_summary_df(df)


def load_schema_summary_from_csv(path: str | Path) -> list[SchemaSummary]:
    df = pd.read_csv(path)
    return _normalize_summary_df(df)


def load_mock_schema_summary() -> list[SchemaSummary]:
    data = [
        {
            "schema_name": "LEGACY_BILLING",
            "environment": "PRO",
            "batch": "L001",
            "manager": "Ana",
            "application": "Billing 9",
            "size_gb": 124.2,
            "object_count": 1400,
            "last_login_days_ago": 430,
            "account_status": "OPEN",
            "active_jobs": 0,
            "apex_applications": 0,
            "external_dependencies": 2,
            "enabled_triggers": 1,
            "recent_activity": False,
        },
        {
            "schema_name": "CRM_CORE",
            "environment": "PRO",
            "batch": "L001",
            "manager": "Luis",
            "application": "CRM",
            "size_gb": 52.3,
            "object_count": 920,
            "last_login_days_ago": 15,
            "account_status": "OPEN",
            "active_jobs": 5,
            "apex_applications": 3,
            "external_dependencies": 8,
            "enabled_triggers": 12,
            "recent_activity": True,
        },
        {
            "schema_name": "ARCHIVE_2014",
            "environment": "PRE",
            "batch": "L009",
            "manager": "Marta",
            "application": "Archive",
            "size_gb": 8.9,
            "object_count": 120,
            "last_login_days_ago": 730,
            "account_status": "LOCKED",
            "active_jobs": 0,
            "apex_applications": 0,
            "external_dependencies": 0,
            "enabled_triggers": 0,
            "recent_activity": False,
        },
    ]
    return [SchemaSummary(**row) for row in data]


def load_followup_from_excel(path: str | Path, sheet_name: str = "followup") -> list[SchemaFollowUp]:
    df = pd.read_excel(path, sheet_name=sheet_name)
    clean_df = df.copy()
    clean_df.columns = [c.strip().lower() for c in clean_df.columns]
    aliases = {
        "schema": "schema_name",
        "esquema": "schema_name",
        "estado": "status",
        "fase": "phase",
        "responsable": "owner",
        "proxima_accion": "next_action",
        "próxima_acción": "next_action",
        "observaciones": "observations",
    }
    clean_df = clean_df.rename(columns={c: aliases.get(c, c) for c in clean_df.columns})
    required = {"schema_name"}
    missing = required - set(clean_df.columns)
    if missing:
        raise ValueError(f"Inventario sin columnas mínimas: {sorted(missing)}")
    return [SchemaFollowUp(**row) for row in clean_df.to_dict(orient="records")]


def load_schema_summary_from_export_files(paths: list[str | Path]) -> list[SchemaSummary]:
    frames: list[pd.DataFrame] = []
    for p in paths:
        suffix = str(p).lower()
        if suffix.endswith(".csv"):
            frames.append(pd.read_csv(p))
        elif suffix.endswith(".xlsx"):
            frames.append(pd.read_excel(p, sheet_name="schema_summary"))
    if not frames:
        return []
    merged = pd.concat(frames, ignore_index=True)
    return _normalize_summary_df(merged)


def _normalize_summary_df(df: pd.DataFrame) -> list[SchemaSummary]:
    cols = {c.strip().lower() for c in df.columns}
    missing = REQUIRED_COLUMNS - cols
    if missing:
        raise ValueError(
            "Faltan columnas en el archivo de entrada. "
            f"Requeridas: {sorted(REQUIRED_COLUMNS)}. Faltantes: {sorted(missing)}"
        )

    clean_df = df.copy()
    clean_df.columns = [c.strip().lower() for c in clean_df.columns]
    clean_df["recent_activity"] = clean_df["recent_activity"].astype(bool)
    return [SchemaSummary(**row) for row in clean_df.to_dict(orient="records")]
