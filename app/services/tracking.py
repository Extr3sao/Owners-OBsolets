from __future__ import annotations

from datetime import date

from app.domain.models import SchemaEvaluation, SchemaFollowUp


def suggest_operational_next_action(evaluation: SchemaEvaluation) -> str:
    if "Bloqueado" in evaluation.classification.value:
        return "Abrir seguimiento con equipo dependiente y validar impacto funcional"
    if evaluation.classification.value == "Candidato probable":
        return "Planificar Fase 3 y validación funcional"
    if evaluation.classification.value == "Apto para limpieza previa":
        return "Preparar backup y ejecutar limpieza previa controlada"
    return "Mantener monitorización y actualizar inventario"


def followup_kpis(items: list[SchemaFollowUp]) -> dict[str, int]:
    today = date.today()
    overdue = 0
    with_owner = 0
    with_due_date = 0
    needs_backup = 0

    for item in items:
        if item.owner:
            with_owner += 1
        if item.due_date is not None:
            with_due_date += 1
            if item.due_date < today and item.status.lower() not in {"cerrado", "completado"}:
                overdue += 1
        if item.needs_backup:
            needs_backup += 1

    return {
        "total": len(items),
        "overdue": overdue,
        "with_owner": with_owner,
        "with_due_date": with_due_date,
        "needs_backup": needs_backup,
    }
