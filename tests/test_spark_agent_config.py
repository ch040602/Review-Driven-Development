from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
