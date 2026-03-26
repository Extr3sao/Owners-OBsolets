from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text


class OracleQueryService:
    """Servicio opcional para ejecutar consultas de solo lectura contra Oracle."""

    def __init__(self, connection_uri: str):
        self.engine = create_engine(connection_uri)

    def execute_query(self, sql_text: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        with self.engine.connect() as conn:
            return pd.read_sql(text(sql_text), conn, params=params)

    @staticmethod
    def read_sql_file(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
