from __future__ import annotations

from app.domain.models import AnalysisRun


CAPABILITY_KEYS = [
    "ingesta_excel",
    "ingesta_csv",
    "ingesta_mocks",
    "oracle_read_only_service",
    "reglas_scoring",
    "bloqueos_duros",
    "seguimiento_operativo",
    "comparativa_runs",
    "reporting_markdown",
    "reporting_html_pdf",
    "conector_oracle_en_ui",
    "inventario_excel_seguimiento",
    "sql_script_source",
]


def project_capability_status() -> dict[str, bool]:
    return {
        "ingesta_excel": True,
        "ingesta_csv": True,
        "ingesta_mocks": True,
        "oracle_read_only_service": True,
        "reglas_scoring": True,
        "bloqueos_duros": True,
        "seguimiento_operativo": True,
        "comparativa_runs": True,
        "reporting_markdown": True,
        "reporting_html_pdf": True,
        "conector_oracle_en_ui": False,
        "inventario_excel_seguimiento": True,
        "sql_script_source": True,
    }


def summarize_gaps(run: AnalysisRun | None = None) -> dict[str, list[str]]:
    status = project_capability_status()
    done = [k for k in CAPABILITY_KEYS if status.get(k)]
    pending = [k for k in CAPABILITY_KEYS if not status.get(k)]

    context = []
    if run:
        context.append(f"run_id={run.run_id}")
        context.append(f"schemas={run.schema_count}")
        context.append(f"source={run.data_source}")

    return {"implemented": done, "pending": pending, "context": context}
