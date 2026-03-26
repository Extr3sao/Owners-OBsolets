# Owners-OBsolets

Aplicación **MVP funcional** para analizar esquemas Oracle potencialmente obsoletos, priorizar riesgos, gestionar seguimiento y generar informes.

## 1) Arquitectura objetivo

La solución sigue arquitectura modular, separando UI, dominio y lógica:

- `app/ui`: componentes Streamlit (en MVP concentrados en `app/main.py`).
- `app/domain`: modelos tipados (Pydantic) y enums funcionales.
- `app/services`: ingesta (mock/CSV/Excel), recomendaciones y cliente Oracle de solo lectura.
- `app/rules`: motor de evaluación desacoplado de UI.
- `app/repositories`: persistencia de ejecuciones y seguimiento.
- `app/reporting`: plantillas Jinja2 para informes Markdown/HTML.
- `app/config`: configuración de reglas/umbrales por YAML.
- `app/tests`: pruebas unitarias del motor.

## 2) Modelo de datos

Entidades incluidas (alineadas con tu requerimiento):

- `SchemaSummary`
- `SchemaObjectStats`
- `RecentObjectChange`
- `DependencyRecord`
- `PrivilegeRecord`
- `SchedulerJob`
- `LegacyJob`
- `ApexApplication`
- `ApexActivity`
- `DbLinkRecord`
- `TriggerRecord`
- `CodeReference`
- `SchemaFollowUp`
- `AnalysisRun`
- `RecommendedAction`
- `SchemaEvaluation` (resultado explicable)

## 3) Motor de reglas y scoring

`RuleEngine` implementa:

- score de obsolescencia (0-100)
- score de riesgo (0-100)
- señales de bloqueo duro
- clasificación final
- severidad
- explicación ejecutiva y técnica
- fase siguiente recomendada

Reglas/umbrales en `app/config/rules.yaml` con fallback a `app/config/rules.json` cuando PyYAML no esté instalado.

## 4) Flujo funcional implementado (MVP)

1. Carga datos (mock/CSV/Excel).
2. Normaliza a `SchemaSummary`.
3. Evalúa con reglas.
4. Presenta dashboard (resumen, ranking, matriz riesgo vs obsolescencia, detalle por esquema y filtros avanzados).
5. Gestiona seguimiento (estado/fase/responsable/observaciones).
6. Guarda ejecución de análisis.
7. Compara ejecuciones previas.
8. Genera informe ejecutivo y técnico (Markdown).

> Seguridad: la aplicación **no ejecuta acciones destructivas**; no hay `DROP`, ni `ALTER` destructivo, ni deshabilitados automáticos.

## 5) Entradas soportadas actualmente

- `Mocks` (sin Oracle, para demo end-to-end)
- `CSV` con columnas normalizadas
- `Excel` (`sheet_name=schema_summary`) con columnas equivalentes
- `Multi-export` para consolidar varios CSV/Excel en una sola ejecución
- `Script SQL` para cargar y revisar sentencias (modo seguro, no ejecución automática)

### Asunción de columnas de entrada (CSV/Excel)

- `schema_name`
- `environment`
- `batch`
- `manager`
- `application`
- `size_gb`
- `object_count`
- `last_login_days_ago`
- `account_status`
- `active_jobs`
- `apex_applications`
- `external_dependencies`
- `enabled_triggers`
- `recent_activity`

Muestra: `app/data/samples/schema_summary_sample.csv`.

## 6) Preparado para Oracle real

Existe cliente `OracleQueryService` (SQLAlchemy + oracledb) para ejecutar consultas de solo lectura y reutilizar scripts SQL base.

## 7) Reporting

- Informe ejecutivo: plantilla `executive_report.md.j2`
- Informe técnico por esquema: plantilla `schema_technical.md.j2`
- Exportación a PDF: preparada vía conversión Markdown/HTML con herramienta externa.

## 8) Arranque local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
streamlit run app/main.py
```

## 9) Tests

```bash
pytest
```

## 10) ¿Cómo saber qué falta?

La UI incluye un bloque **“Cobertura funcional (implementado vs pendiente)”** que muestra capacidades completadas y pendientes en tiempo real para facilitar el seguimiento de evolución del MVP.

## 11) Mejoras adicionales incluidas

- Carga opcional de inventario de seguimiento desde Excel (`sheet_name=followup`) para precargar estado/fase/responsable.
- Exportación de informe ejecutivo también en HTML, lista para conversión a PDF con herramientas externas.
- Comparativa entre ejecuciones con KPIs de cambios de estado, subidas/bajadas de riesgo y nuevos candidatos.
- Seguimiento reforzado con prioridad, fecha objetivo, tags y resultado por esquema.
- Historial de eventos operativo por esquema (comentarios, validaciones, cambios de fase, riesgos, dependencias resueltas).
