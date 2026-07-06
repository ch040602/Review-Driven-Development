from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from toml_compat import loads_toml, loads_toml_minimal  # noqa: E402


def test_minimal_toml_loader_parses_agent_config() -> None:
    text = (REPO_ROOT / ".codex" / "agents" / "rdd-spark-critic.toml").read_text(encoding="utf-8")

    data = loads_toml_minimal(text)

    assert data["name"] == "rdd_spark_critic"
    assert data["model"] == "gpt-5.3-codex-spark"
    assert data["sandbox_mode"] == "read-only"
    assert "Do not implement patches." in data["developer_instructions"]


def test_toml_loader_parses_pyproject_optional_dependencies() -> None:
    text = """
[project.optional-dependencies]
semantic = [
    "scikit-learn>=1.4",
    "requests>=2",
]
"""

    data = loads_toml(text)

    assert data["project"]["optional-dependencies"]["semantic"] == ["scikit-learn>=1.4", "requests>=2"]
