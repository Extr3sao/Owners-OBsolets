from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from app.config.settings import load_rules_config
from app.domain.models import AnalysisRun, FollowUpEvent, SchemaFollowUp
from app.reporting.report_generator import (
    render_executive_report,
    render_executive_report_html,
    render_technical_report,
)
from app.repositories.followup_repository import FollowUpRepository
from app.repositories.followup_event_repository import FollowUpEventRepository
from app.repositories.run_repository import RunRepository, build_run_id, compare_runs, compare_runs_summary
from app.rules.evaluator import RuleEngine
from app.services.ingestion import (
    load_followup_from_excel,
    load_mock_schema_summary,
    load_schema_summary_from_export_files,
    load_schema_summary_from_csv,
    load_schema_summary_from_excel,
)
from app.services.gap_analysis import summarize_gaps
from app.services.recommendations import build_recommendations
from app.services.sql_parser import split_sql_statements
from app.services.tracking import followup_kpis, suggest_operational_next_action

st.set_page_config(page_title="Owners Obsolets", layout="wide")
st.title("Owners Obsolets - Análisis de esquemas Oracle")

rules_cfg = load_rules_config()
engine = RuleEngine(rules_cfg)
run_repo = RunRepository()
follow_repo = FollowUpRepository()
event_repo = FollowUpEventRepository()

source = st.sidebar.selectbox("Fuente de datos", ["Mocks", "Excel", "CSV", "Multi-export", "Script SQL"])

schemas = []
if source == "Mocks":
    schemas = load_mock_schema_summary()
elif source == "Excel":
    file = st.sidebar.file_uploader("Sube Excel", type=["xlsx"])
    if file:
        schemas = load_schema_summary_from_excel(file)
elif source == "CSV":
    file = st.sidebar.file_uploader("Sube CSV", type=["csv"])
    if file:
        schemas = load_schema_summary_from_csv(file)
elif source == "Multi-export":
    files = st.sidebar.file_uploader(
        "Sube múltiples exportaciones (.csv/.xlsx)", type=["csv", "xlsx"], accept_multiple_files=True
    )
    if files:
        schemas = load_schema_summary_from_export_files(files)
elif source == "Script SQL":
    sql_file = st.sidebar.file_uploader("Sube script SQL", type=["sql"])
    if sql_file:
        statements = split_sql_statements(sql_file.getvalue().decode("utf-8", errors="ignore"))
        st.info(
            f"Script cargado con {len(statements)} sentencias. "
            "Modo seguro: no se ejecuta automáticamente, solo revisión."
        )
        st.code("\n;\n".join(statements[:3]), language="sql")

inventory_file = st.sidebar.file_uploader("Inventario seguimiento Excel (opcional)", type=["xlsx"])

if not schemas:
    st.info("Carga datos para continuar.")
    st.stop()

evaluations = [engine.evaluate(s) for s in schemas]
run = AnalysisRun(
    run_id=build_run_id(),
    run_ts=datetime.now(timezone.utc),
    environment="MULTI",
    data_source=source,
    rules_version=rules_cfg["version"],
    schema_count=len(schemas),
    evaluations=evaluations,
)

df = pd.DataFrame(
    [
        {
            "schema_name": e.schema_name,
            "environment": s.environment,
            "batch": s.batch,
            "manager": s.manager,
            "application": s.application,
            "active_jobs": s.active_jobs,
            "apex_applications": s.apex_applications,
            "external_dependencies": s.external_dependencies,
            "recent_activity": s.recent_activity,
            "classification": e.classification.value,
            "severity": e.severity.value,
            "obsolescence_score": e.obsolescence_score,
            "risk_score": e.risk_score,
            "next_phase": e.next_phase,
            "blocking": ", ".join(e.blocking_signals),
        }
        for e, s in zip(evaluations, schemas)
    ]
)

st.sidebar.markdown("### Filtros")
env_filter = st.sidebar.multiselect("Entorno", sorted(df["environment"].unique()), default=list(df["environment"].unique()))
batch_filter = st.sidebar.multiselect("Lote", sorted(df["batch"].unique()), default=list(df["batch"].unique()))
manager_filter = st.sidebar.multiselect("Gestor", sorted(df["manager"].unique()), default=list(df["manager"].unique()))
severity_filter = st.sidebar.multiselect("Severidad", sorted(df["severity"].unique()), default=list(df["severity"].unique()))
phase_filter = st.sidebar.multiselect("Fase", sorted(df["next_phase"].unique()), default=list(df["next_phase"].unique()))
only_blocked = st.sidebar.checkbox("Solo bloqueados", value=False)
has_apex = st.sidebar.selectbox("Tiene APEX", ["Todos", "Sí", "No"], index=0)
has_jobs = st.sidebar.selectbox("Tiene jobs", ["Todos", "Sí", "No"], index=0)
has_deps = st.sidebar.selectbox("Tiene dependencias", ["Todos", "Sí", "No"], index=0)
has_recent_activity = st.sidebar.selectbox("Actividad reciente", ["Todos", "Sí", "No"], index=0)

filtered_df = df[
    df["environment"].isin(env_filter)
    & df["batch"].isin(batch_filter)
    & df["manager"].isin(manager_filter)
    & df["severity"].isin(severity_filter)
    & df["next_phase"].isin(phase_filter)
]
if only_blocked:
    filtered_df = filtered_df[filtered_df["classification"].str.contains("Bloqueado")]
if has_apex != "Todos":
    filtered_df = filtered_df[filtered_df["apex_applications"].gt(0) if has_apex == "Sí" else filtered_df["apex_applications"].eq(0)]
if has_jobs != "Todos":
    filtered_df = filtered_df[filtered_df["active_jobs"].gt(0) if has_jobs == "Sí" else filtered_df["active_jobs"].eq(0)]
if has_deps != "Todos":
    filtered_df = filtered_df[
        filtered_df["external_dependencies"].gt(0) if has_deps == "Sí" else filtered_df["external_dependencies"].eq(0)
    ]
if has_recent_activity != "Todos":
    filtered_df = filtered_df[
        filtered_df["recent_activity"].eq(True) if has_recent_activity == "Sí" else filtered_df["recent_activity"].eq(False)
    ]

st.header("Resumen ejecutivo")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total esquemas", len(filtered_df))
c2.metric("Candidatos", int((filtered_df["classification"] == "Candidato probable").sum()))
c3.metric("Bloqueados", int(filtered_df["classification"].str.contains("Bloqueado").sum()))
c4.metric("Críticos", int((filtered_df["severity"] == "Crítica").sum()))

st.subheader("Matriz riesgo vs obsolescencia")
fig = px.scatter(
    filtered_df,
    x="obsolescence_score",
    y="risk_score",
    color="classification",
    size="risk_score",
    hover_name="schema_name",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Ranking")
tab1, tab2 = st.tabs(["Mayor obsolescencia", "Mayor riesgo"])
with tab1:
    st.dataframe(filtered_df.sort_values("obsolescence_score", ascending=False).head(10), use_container_width=True)
with tab2:
    st.dataframe(filtered_df.sort_values("risk_score", ascending=False).head(10), use_container_width=True)

st.subheader("Detalle por esquema")
selected = st.selectbox("Esquema", filtered_df["schema_name"].tolist() if not filtered_df.empty else df["schema_name"].tolist())
ev = next(e for e in evaluations if e.schema_name == selected)
st.write(ev.executive_summary)
st.write(ev.technical_detail)
st.json(ev.model_dump())
st.markdown("### Checklist recomendada")
for rec in build_recommendations(ev):
    st.checkbox(rec.action, value=False, key=f"{selected}_{rec.action}")

st.subheader("Seguimiento")
existing = {f.schema_name: f for f in follow_repo.load()}
if inventory_file:
    for inv in load_followup_from_excel(inventory_file):
        existing[inv.schema_name] = inv
    st.sidebar.success("Inventario cargado en seguimiento.")
f_item = existing.get(selected, SchemaFollowUp(schema_name=selected))
f_kpis = followup_kpis(list(existing.values()))
fk1, fk2, fk3, fk4, fk5 = st.columns(5)
fk1.metric("Items seguimiento", f_kpis["total"])
fk2.metric("Con responsable", f_kpis["with_owner"])
fk3.metric("Con fecha objetivo", f_kpis["with_due_date"])
fk4.metric("Vencidos", f_kpis["overdue"])
fk5.metric("Requieren backup", f_kpis["needs_backup"])

default_action = suggest_operational_next_action(ev)
with st.form("followup_form"):
    f_item.status = st.text_input("Estado", value=f_item.status)
    f_item.phase = st.text_input("Fase", value=f_item.phase)
    f_item.priority = st.selectbox("Prioridad", ["Baja", "Media", "Alta", "Crítica"], index=["Baja", "Media", "Alta", "Crítica"].index(f_item.priority if f_item.priority in ["Baja", "Media", "Alta", "Crítica"] else "Media"))
    f_item.owner = st.text_input("Responsable", value=f_item.owner)
    f_item.next_action = st.text_input("Próxima acción", value=f_item.next_action or default_action)
    f_item.due_date = st.date_input("Fecha objetivo", value=f_item.due_date or datetime.now(timezone.utc).date())
    f_item.tags = st.text_input("Tags", value=f_item.tags)
    f_item.observations = st.text_area("Observaciones", value=f_item.observations)
    f_item.result = st.text_input("Resultado", value=f_item.result)
    submitted = st.form_submit_button("Guardar seguimiento")
if submitted:
    existing[selected] = f_item
    follow_repo.save(list(existing.values()))
    st.success("Seguimiento guardado")

st.markdown("#### Historial de eventos de seguimiento")
with st.form("event_form"):
    event_type = st.selectbox(
        "Tipo de evento",
        ["Comentario", "Validación funcional", "Cambio de fase", "Riesgo detectado", "Dependencia resuelta"],
    )
    actor = st.text_input("Actor", value=f_item.owner)
    note = st.text_area("Detalle del evento")
    add_event = st.form_submit_button("Registrar evento")
if add_event and note.strip():
    event_repo.add_event(
        FollowUpEvent(
            schema_name=selected,
            event_ts=datetime.now(timezone.utc),
            event_type=event_type,
            actor=actor or "N/A",
            note=note.strip(),
        )
    )
    st.success("Evento registrado")

events = event_repo.list_for_schema(selected)
if events:
    ev_df = pd.DataFrame([e.model_dump() for e in events]).sort_values("event_ts", ascending=False)
    st.dataframe(ev_df, use_container_width=True)
else:
    st.caption("No hay eventos registrados para este esquema.")

st.subheader("Comparativa de ejecuciones")
runs = run_repo.list_runs()
if runs:
    old_run_id = st.selectbox("Run anterior", runs)
    if st.button("Comparar"):
        old_run = run_repo.load(old_run_id)
        cmp_df = compare_runs(old_run, run)
        cmp_summary = compare_runs_summary(old_run, run)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cambios de estado", cmp_summary["state_changes"])
        c2.metric("Nuevos candidatos", cmp_summary["new_candidates"])
        c3.metric("Subidas de riesgo", cmp_summary["risk_increase"])
        c4.metric("Bajadas de riesgo", cmp_summary["risk_decrease"])
        st.dataframe(cmp_df, use_container_width=True)
else:
    st.caption("Sin ejecuciones previas guardadas")

st.subheader("Cobertura funcional (implementado vs pendiente)")
gap_summary = summarize_gaps(run)
g1, g2 = st.columns(2)
with g1:
    st.markdown("**Implementado**")
    for item in gap_summary["implemented"]:
        st.write(f"✅ {item}")
with g2:
    st.markdown("**Pendiente**")
    for item in gap_summary["pending"]:
        st.write(f"⚠️ {item}")

if st.button("Guardar ejecución"):
    path = run_repo.save(run)
    st.success(f"Ejecución guardada en {path}")

st.subheader("Reporting")
if st.button("Generar informe ejecutivo (Markdown)"):
    content = render_executive_report(run)
    st.download_button("Descargar", content, file_name=f"{run.run_id}_executive.md")

if st.button("Generar informe ejecutivo (HTML)"):
    html_content = render_executive_report_html(run)
    st.download_button("Descargar HTML", html_content, file_name=f"{run.run_id}_executive.html")

if st.button("Generar informe técnico del esquema seleccionado"):
    content = render_technical_report(ev)
    st.download_button("Descargar técnico", content, file_name=f"{selected}_technical.md")

st.caption("Nota: exportación a PDF preparada vía HTML/Markdown + motor externo (wkhtmltopdf/weasyprint).")
