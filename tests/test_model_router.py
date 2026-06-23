from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "review-driven-development" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from model_router import build_spawn_plan, route_role  # noqa: E402


def test_model_router_maps_simplification_to_spark_agent() -> None:
    route = route_role("simplification-critic", phase="validation")

    assert route["custom_agent_name"] == "rdd_spark_critic"
    assert route["model"] == "gpt-5.3-codex-spark"
    assert route["sandbox"] == "read-only"


def test_model_router_escalates_security_to_deep_agent() -> None:
    route = route_role("security-risk-critic", phase="preplan", critic_depth="deep")

    assert route["custom_agent_name"] == "rdd_deep_critic"
    assert route["model"] == "gpt-5.5"


def test_model_router_builds_spawn_plan_without_claiming_execution(tmp_path: Path) -> None:
    brief = tmp_path / "simplification-critic.md"
    brief.write_text("# brief\n", encoding="utf-8")

    plan = build_spawn_plan([brief], phase="validation")

    assert plan[0]["role"] == "simplification-critic"
    assert plan[0]["brief_path"] == str(brief)
    assert plan[0]["instruction"] == "Spawn manually only when the main agent decides the token cost is justified."
