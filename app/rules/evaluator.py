from __future__ import annotations

from app.domain.models import Classification, SchemaEvaluation, SchemaSummary, Severity


class RuleEngine:
    def __init__(self, config: dict):
        self.config = config
        self.thresholds = config["thresholds"]
        self.weights = config["weights"]

    def evaluate(self, schema: SchemaSummary) -> SchemaEvaluation:
        obsolescence_score = self._obsolescence_score(schema)
        risk_score = self._risk_score(schema)

        triggered, blocking = self._rules(schema)
        classification = self._classify(schema, blocking, obsolescence_score, risk_score)
        severity = self._severity(risk_score)

        next_phase = self._next_phase(classification)
        decision = "No ejecutar acciones destructivas; continuar seguimiento y validación"
        executive = (
            f"El esquema {schema.schema_name} queda clasificado como {classification.value} "
            f"porque presenta {', '.join(blocking[:3]) if blocking else 'baja evidencia de uso reciente'}."
        )
        technical = (
            f"Obsolescencia={obsolescence_score}, Riesgo={risk_score}, "
            f"Reglas={len(triggered)}, Bloqueos={len(blocking)}"
        )
        return SchemaEvaluation(
            schema_name=schema.schema_name,
            obsolescence_score=obsolescence_score,
            risk_score=risk_score,
            severity=severity,
            classification=classification,
            triggered_rules=triggered,
            blocking_signals=blocking,
            executive_summary=executive,
            technical_detail=technical,
            next_phase=next_phase,
            decision=decision,
        )

    def _obsolescence_score(self, s: SchemaSummary) -> int:
        w = self.weights["obsolescence"]
        score = 0
        if s.last_login_days_ago > self.thresholds["green_last_login_days"]:
            score += w["inactivity"]
        if s.active_jobs == 0:
            score += w["no_jobs"]
        if s.apex_applications == 0:
            score += w["no_apex"]
        if s.external_dependencies == 0:
            score += w["no_external_dependencies"]
        if s.account_status.upper() in {"LOCKED", "EXPIRED", "LOCKED(TIMED)"}:
            score += w["account_locked_or_expired"]
        return min(score, 100)

    def _risk_score(self, s: SchemaSummary) -> int:
        w = self.weights["risk"]
        score = 0
        if s.recent_activity or s.last_login_days_ago < 90:
            score += w["recent_activity"]
        if s.active_jobs > 0:
            score += w["active_jobs"]
        if s.apex_applications > 0:
            score += w["apex_recent"]
        if s.external_dependencies > 0:
            score += w["external_dependencies"]
        if s.enabled_triggers > 0:
            score += w["enabled_triggers"]
        return min(score, 100)

    def _rules(self, s: SchemaSummary) -> tuple[list[str], list[str]]:
        triggered: list[str] = []
        blocking: list[str] = []
        if s.last_login_days_ago > 365 and s.active_jobs == 0 and s.apex_applications == 0:
            triggered.append("Semáforo verde preliminar")
        if s.last_login_days_ago < 90:
            triggered.append("Acceso reciente")
            blocking.append("actividad reciente")
        if s.active_jobs > 0:
            triggered.append("Jobs activos")
            blocking.append("jobs activos o recientes")
        if s.apex_applications > 0:
            triggered.append("APEX activo")
            blocking.append("actividad APEX reciente")
        if s.external_dependencies > 0:
            triggered.append("Dependencias externas")
            blocking.append("dependencias externas no resueltas")
        if s.enabled_triggers > 0:
            triggered.append("Triggers enabled")
            blocking.append("triggers automáticos enabled")
        if s.recent_activity:
            triggered.append("Actividad objeto/código reciente")
            if "actividad reciente" not in blocking:
                blocking.append("actividad reciente")
        return triggered, blocking

    def _classify(
        self,
        s: SchemaSummary,
        blocking: list[str],
        obsolescence_score: int,
        risk_score: int,
    ) -> Classification:
        if any("dependencias" in b for b in blocking):
            return Classification.BLOCKED_DEPENDENCY
        if any("actividad" in b or "jobs" in b or "APEX" in b for b in blocking):
            return Classification.BLOCKED_ACTIVITY
        if obsolescence_score >= 70 and risk_score <= 25:
            return Classification.READY_PRE_CLEANUP
        if obsolescence_score >= 55 and risk_score <= 40:
            return Classification.PROBABLE_CANDIDATE
        if s.last_login_days_ago < self.thresholds["yellow_last_login_days"]:
            return Classification.NOT_OBSOLETE
        return Classification.UNDER_REVIEW

    def _severity(self, risk_score: int) -> Severity:
        if risk_score > self.config["severities"]["high_max"]:
            return Severity.CRITICAL
        if risk_score > self.config["severities"]["medium_max"]:
            return Severity.HIGH
        if risk_score > self.config["severities"]["low_max"]:
            return Severity.MEDIUM
        return Severity.LOW

    def _next_phase(self, classification: Classification) -> str:
        if classification in {Classification.BLOCKED_DEPENDENCY, Classification.BLOCKED_ACTIVITY}:
            return "Fase 2: Verificación de dependencias"
        if classification in {Classification.PROBABLE_CANDIDATE, Classification.UNDER_REVIEW}:
            return "Fase 3: Revisión de actividad"
        if classification == Classification.READY_PRE_CLEANUP:
            return "Fase 4: Limpieza previa"
        return "Fase 1: Análisis inicial"
