from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_rules_config(
    yaml_path: str | Path = "app/config/rules.yaml",
    json_fallback_path: str | Path = "app/config/rules.json",
) -> dict[str, Any]:
    yaml_file = Path(yaml_path)
    if yaml_file.exists():
        try:
            import yaml  # optional dependency

            with yaml_file.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        except ModuleNotFoundError:
            pass

    with Path(json_fallback_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)
