from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class Classification(str, Enum):
    NOT_EVALUATED = "No evaluado"
    PROBABLE_CANDIDATE = "Candidato probable"
    UNDER_REVIEW = "En revisión"
    BLOCKED_DEPENDENCY = "Bloqueado por dependencia"
    BLOCKED_ACTIVITY = "Bloqueado por actividad"
    REQUIRES_FUNCTIONAL_VALIDATION = "Requiere validación funcional"
    READY_PRE_CLEANUP = "Apto para limpieza previa"
    READY_PLANNED_REMOVAL = "Apto para eliminación planificada"
    NOT_OBSOLETE = "No obsoleto"


class Severity(str, Enum):
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"
    CRITICAL = "Crítica"


class SchemaSummary(BaseModel):
    schema_name: str
    environment: str = "INT"
    batch: str = "N/A"
    manager: str = "N/A"
    application: str = "N/A"
    created_at: date | None = None
    size_gb: float = 0.0
    object_count: int = 0
    last_login_days_ago: int = 9999
    account_status: str = "UNKNOWN"
    active_jobs: int = 0
    apex_applications: int = 0
    external_dependencies: int = 0
    enabled_triggers: int = 0
    recent_activity: bool = False


class DependencyRecord(BaseModel):
    schema_name: str
    referenced_by_schema: str
    object_name: str
    dependency_type: str
    is_external: bool = True


class SchedulerJob(BaseModel):
    schema_name: str
    job_name: str
    enabled: bool
    last_run_days_ago: int | None = None


class ApexApplication(BaseModel):
    schema_name: str
    app_id: str
    app_name: str
    last_activity_days_ago: int | None = None


class TriggerRecord(BaseModel):
    schema_name: str
    trigger_name: str
    enabled: bool


class CodeReference(BaseModel):
    schema_name: str
    referenced_from: str
    object_name: str
    evidence: str


class SchemaFollowUp(BaseModel):
    schema_name: str
    status: str = "Pendiente"
    phase: str = "Fase 1: Análisis inicial"
    observations: str = ""
    owner: str = ""
    next_action: str = ""
    review_date: date | None = None
    result: str = ""
    needs_backup: bool = True
    needs_functional_validation: bool = True
    needs_rollback_plan: bool = True
    needs_formal_retirement: bool = True
    priority: str = "Media"
    due_date: date | None = None
    tags: str = ""


class FollowUpEvent(BaseModel):
    schema_name: str
    event_ts: datetime
    event_type: str
    actor: str
    note: str


class RecommendedAction(BaseModel):
    schema_name: str
    action: str
    mandatory: bool = True


class SchemaEvaluation(BaseModel):
    schema_name: str
    obsolescence_score: int
    risk_score: int
    severity: Severity
    classification: Classification
    triggered_rules: List[str] = Field(default_factory=list)
    blocking_signals: List[str] = Field(default_factory=list)
    executive_summary: str
    technical_detail: str
    next_phase: str
    decision: str


class AnalysisRun(BaseModel):
    run_id: str
    run_ts: datetime
    environment: str
    data_source: str
    rules_version: str
    schema_count: int
    evaluations: List[SchemaEvaluation] = Field(default_factory=list)


class SchemaObjectStats(BaseModel):
    schema_name: str
    object_type: str
    object_count: int


class RecentObjectChange(BaseModel):
    schema_name: str
    object_name: str
    object_type: str
    ddl_days_ago: int


class PrivilegeRecord(BaseModel):
    schema_name: str
    privilege: str
    grantee: str


class LegacyJob(BaseModel):
    schema_name: str
    job_id: str
    last_run_days_ago: int | None = None


class ApexActivity(BaseModel):
    schema_name: str
    app_id: str
    activity_days_ago: int


class DbLinkRecord(BaseModel):
    schema_name: str
    db_link_name: str
    target: str
