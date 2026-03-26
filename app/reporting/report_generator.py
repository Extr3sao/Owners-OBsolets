from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.domain.models import AnalysisRun, SchemaEvaluation


def _env() -> Environment:
    template_dir = Path("app/reporting/templates")
    template_dir.mkdir(parents=True, exist_ok=True)
    return Environment(
        loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"])
    )


def render_executive_report(run: AnalysisRun) -> str:
    tpl = _env().get_template("executive_report.md.j2")
    return tpl.render(run=run)


def render_technical_report(eval_result: SchemaEvaluation) -> str:
    tpl = _env().get_template("schema_technical.md.j2")
    return tpl.render(ev=eval_result)


def render_executive_report_html(run: AnalysisRun) -> str:
    tpl = _env().get_template("executive_report.html.j2")
    return tpl.render(run=run)


def write_report(content: str, out_path: str) -> None:
    Path(out_path).write_text(content, encoding="utf-8")
