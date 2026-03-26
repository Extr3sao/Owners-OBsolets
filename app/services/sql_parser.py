from __future__ import annotations


def split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL script into simple statements by ';' ignoring empty chunks."""
    parts = [p.strip() for p in sql_text.split(";")]
    return [p for p in parts if p]
