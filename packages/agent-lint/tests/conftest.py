from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = REPO_ROOT / "docs" / "schemas"


@pytest.fixture(scope="session")
def finding_schema() -> dict[str, Any]:
    schema_path = SCHEMAS_DIR / "finding-v1.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def validate_finding_dict(finding_schema: dict[str, Any]):
    def _validate(data: dict[str, Any]) -> None:
        jsonschema.validate(instance=data, schema=finding_schema)

    return _validate
