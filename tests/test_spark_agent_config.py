from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from toml_compat import loads_toml  # noqa: E402


def test_spark_agent_config_uses_codex_spark_read_only() -> None:
    path = REPO_ROOT / ".codex" / "agents" / "rdd-spark-critic.toml"
    data = loads_toml(path.read_text(encoding="utf-8"))

    assert data["name"] == "rdd_spark_critic"
    assert data["model"] == "gpt-5.3-codex-spark"
    assert data["sandbox_mode"] == "read-only"
    assert "Do not implement patches." in data["developer_instructions"]


def test_low_effort_spark_agent_config_matches_minimal_routes() -> None:
    path = REPO_ROOT / ".codex" / "agents" / "rdd-spark-low-critic.toml"
    data = loads_toml(path.read_text(encoding="utf-8"))

    assert data["name"] == "rdd_spark_low_critic"
    assert data["model"] == "gpt-5.3-codex-spark"
    assert data["model_reasoning_effort"] == "low"
    assert data["sandbox_mode"] == "read-only"


@pytest.mark.parametrize(
    ("filename", "expected_effort", "expected_name"),
    [
        ("rdd-standard-critic.toml", "high", "rdd_standard_critic"),
        ("rdd-deep-critic.toml", "max", "rdd_deep_critic"),
    ],
)
def test_reasoning_critic_configs_share_gpt_56_with_different_effort(
    filename: str,
    expected_effort: str,
    expected_name: str,
) -> None:
    path = REPO_ROOT / ".codex" / "agents" / filename
    data = loads_toml(path.read_text(encoding="utf-8"))

    assert data["name"] == expected_name
    assert data["model"] == "gpt-5.6"
    assert data["model_reasoning_effort"] == expected_effort
    assert data["sandbox_mode"] == "read-only"


def test_hooks_json_uses_matcher_group_schema() -> None:
    path = REPO_ROOT / ".codex" / "hooks.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    pre_tool = data["hooks"]["PreToolUse"][0]
    assert "hooks" in pre_tool
    assert pre_tool["hooks"][0]["type"] == "command"
    assert "rdd_pre_tool_use.py" in pre_tool["hooks"][0]["command"]


def test_stop_hook_emits_valid_stop_json() -> None:
    script = REPO_ROOT / ".codex" / "hooks" / "rdd_stop_check.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        input='{"hook_event_name":"Stop"}',
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload == {"continue": True}
    assert "TODO completion needs validation evidence" in result.stderr


def test_subagent_hook_keeps_unmarked_routes_critical_only() -> None:
    script = REPO_ROOT / ".codex" / "hooks" / "rdd_subagent_start.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        input='{"prompt":"review this brief"}',
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=True,
    )

    assert "critical-only, no patches" in result.stdout


def test_subagent_hook_allows_only_explicit_bounded_implementation_routes() -> None:
    script = REPO_ROOT / ".codex" / "hooks" / "rdd_subagent_start.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps({"prompt": "task_kind: simple-implementation\ncontract: implementation"}),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        check=True,
    )

    assert "bounded implementation" in result.stdout
    assert "critical-only, no patches" not in result.stdout
