from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT if (REPO_ROOT / "SKILL.md").exists() else REPO_ROOT / "skills" / "review-driven-development"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from model_router import build_spawn_plan, load_routing_policy, route_role, route_task, validate_routing_policy  # noqa: E402


def test_default_policy_uses_only_gpt_56_and_codex_spark() -> None:
    policy = load_routing_policy()

    assert {model["id"] for model in policy["models"]} == {
        "gpt-5.3-codex-spark",
        "gpt-5.6",
    }


def test_simple_implementation_routes_to_spark_by_capability() -> None:
    route = route_task("simple-implementation", phase="execution")

    assert route["route_status"] == "selected"
    assert route["model"] == "gpt-5.3-codex-spark"
    assert route["reasoning_effort"] == "low"
    assert route["required_capabilities"] == ["simple-implementation"]
    assert route["custom_agent_name"] == ""


def test_logic_design_routes_to_gpt_56_high() -> None:
    route = route_task("logic-design", phase="execution")

    assert route["route_status"] == "selected"
    assert route["model"] == "gpt-5.6"
    assert route["reasoning_effort"] == "high"
    assert route["complexity"] == "cross-file"


def test_catalog_can_swap_model_ids_without_router_code_changes() -> None:
    policy = copy.deepcopy(load_routing_policy())
    policy["models"][0]["id"] = "fast-local-model"
    policy["models"][1]["id"] = "reasoning-model"

    simple = route_task("simple-implementation", phase="execution", routing_policy=policy)
    logic = route_task("logic-design", phase="execution", routing_policy=policy)

    assert simple["model"] == "fast-local-model"
    assert logic["model"] == "reasoning-model"


def test_policy_rejects_custom_agent_effort_mismatch() -> None:
    policy = copy.deepcopy(load_routing_policy())
    policy["models"][0]["critic_agents"]["max"] = "invalid_spark_max_agent"

    with pytest.raises(ValueError, match="critic_agents.*unsupported effort"):
        validate_routing_policy(policy)


def test_model_router_maps_simplification_to_spark_agent() -> None:
    route = route_role("simplification-critic", phase="validation")

    assert route["custom_agent_name"] == "rdd_spark_critic"
    assert route["model"] == "gpt-5.3-codex-spark"
    assert route["reasoning_effort"] == "medium"
    assert route["sandbox"] == "read-only"


def test_route_does_not_claim_a_static_agent_when_effort_has_no_exact_config() -> None:
    route = route_role("source-grounding-critic", phase="preplan", critic_depth="minimal")

    assert route["model"] == "gpt-5.6"
    assert route["reasoning_effort"] == "medium"
    assert route["custom_agent_name"] == ""


def test_model_router_escalates_security_to_deep_agent() -> None:
    route = route_role(
        "security-risk-critic",
        phase="preplan",
        critic_depth="deep",
        agent_budget="deep",
    )

    assert route["custom_agent_name"] == "rdd_deep_critic"
    assert route["model"] == "gpt-5.6"
    assert route["reasoning_effort"] == "max"


def test_available_models_block_logic_design_when_only_spark_exists() -> None:
    route = route_task(
        "logic-design",
        phase="execution",
        available_models=["gpt-5.3-codex-spark"],
    )

    assert route["route_status"] == "unavailable"
    assert route["model"] == ""
    assert route["fallbacks"] == []
    assert "current main agent" in route["fallback_action"]


def test_budget_does_not_silently_downgrade_max_reasoning() -> None:
    route = route_role(
        "security-risk-critic",
        phase="preplan",
        critic_depth="deep",
        agent_budget="balanced",
    )

    assert route["route_status"] == "budget_limited"
    assert route["required_reasoning_effort"] == "max"
    assert route["model"] == ""
    assert route["reasoning_effort"] == ""


def test_simple_route_exposes_bounded_fallback_chain() -> None:
    route = route_task("simple-implementation", phase="execution")

    assert route["fallbacks"] == [
        {
            "agent_tier": "codex-standard",
            "custom_agent_name": "",
            "estimated_cost_units": 3,
            "model": "gpt-5.6",
            "reasoning_effort": "low",
        }
    ]
    assert route["budget"]["max_fallbacks"] == 1


def test_model_router_builds_spawn_plan_without_claiming_execution(tmp_path: Path) -> None:
    brief = tmp_path / "simplification-critic.md"
    brief.write_text("# brief\n", encoding="utf-8")

    plan = build_spawn_plan([brief], phase="validation")

    assert plan[0]["role"] == "simplification-critic"
    assert plan[0]["brief_path"] == str(brief)
    assert plan[0]["instruction"] == "Spawn manually only when the main agent decides the token cost is justified."


def test_spawn_plan_enforces_total_budget(tmp_path: Path) -> None:
    briefs = []
    for role in ["requirements-critic", "test-tdd-critic"]:
        brief = tmp_path / f"{role}.md"
        brief.write_text("# brief\n", encoding="utf-8")
        briefs.append(brief)

    plan = build_spawn_plan(
        briefs,
        phase="preplan",
        max_plan_cost_units=2,
    )

    assert plan[0]["route_status"] == "selected"
    assert plan[0]["plan_budget"]["spent_after"] == 2
    assert plan[1]["route_status"] == "plan_budget_exceeded"
    assert plan[1]["model"] == ""
    assert plan[1]["blocked_model"] == "gpt-5.3-codex-spark"
    assert plan[1]["budget"]["max_plan_cost_units"] == 2
    assert "aggregate plan budget" in plan[1]["selection_reason"]
