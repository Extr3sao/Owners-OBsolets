from __future__ import annotations

from app.domain.models import RecommendedAction, SchemaEvaluation

BASE_CHECKLIST = [
    "revisar dependencias externas",
    "validar con gestor funcional",
    "revisar actividad reciente",
    "verificar jobs Scheduler",
    "verificar DBMS_JOB",
    "revisar APEX y logs de acceso",
    "revisar triggers enabled",
    "revisar synonyms",
    "revisar grants y roles",
    "preparar backup de objetos",
    "valorar backup de datos",
    "actualizar inventario",
    "abrir seguimiento",
    "monitorizar tras limpieza previa",
    "preparar plan de rollback",
    "planificar ventana de eliminación",
]


def build_recommendations(evaluation: SchemaEvaluation) -> list[RecommendedAction]:
    actions: list[RecommendedAction] = []
    for action in BASE_CHECKLIST:
        mandatory = any(
            k in action
            for k in ["dependencias", "actividad", "APEX", "backup", "rollback", "gestor funcional"]
        )
        actions.append(
            RecommendedAction(
                schema_name=evaluation.schema_name,
                action=action,
                mandatory=mandatory,
            )
        )
    return actions
