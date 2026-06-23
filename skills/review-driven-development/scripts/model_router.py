#!/usr/bin/env python3
"""Map RDD critic roles to Codex custom agent configs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

SPARK_MODEL = "gpt-5.3-codex-spark"
STANDARD_MODEL = "gpt-5.4-mini"
DEEP_MODEL = "gpt-5.5"

SPARK_ROLES = {
    "requirements-critic",
    "test-tdd-critic",
    "documentation-critic",
    "markdown-doc-context-critic",
    "validation-runner-critic",
    "maintainability-critic",
    "quality-critic",
    "simplification-critic",
}
STANDARD_ROLES = {
    "language-runtime-critic",
    "existing-code-reuse-refactor-critic",
    "source-driven-framework-critic",
    "source-grounding-critic",
    "performance-efficiency-critic",
    "accuracy-evaluation-critic",
}
DEEP_ROLES = {"architecture-critic", "security-risk-critic", "data-csv-critic"}


def route_role(role: str, *, phase: str, critic_depth: str = "standard", agent_budget: str = "spark-first") -> Dict[str, Any]:
    """Return the custom-agent routing plan for one role."""

    if role in DEEP_ROLES and (critic_depth == "deep" or agent_budget == "deep"):
        return {
            "role": role,
            "phase": phase,
            "custom_agent_name": "rdd_deep_critic",
            "model": DEEP_MODEL,
            "sandbox": "read-only",
            "escalate_to": "",
            "escalate_when": ["already_deep"],
        }
    if role in DEEP_ROLES or role in STANDARD_ROLES:
        return {
            "role": role,
            "phase": phase,
            "custom_agent_name": "rdd_standard_critic",
            "model": STANDARD_MODEL,
            "sandbox": "read-only",
            "escalate_to": "rdd_deep_critic",
            "escalate_when": ["blocker", "high", "security_data_architecture_uncertainty"],
        }
    return {
        "role": role,
        "phase": phase,
        "custom_agent_name": "rdd_spark_critic",
        "model": SPARK_MODEL,
        "sandbox": "read-only",
        "escalate_to": "rdd_standard_critic",
        "escalate_when": ["blocker", "high", "cross_file_uncertainty"],
    }


def role_from_brief_path(path: Path) -> str:
    """Infer role from a generated brief path."""

    return path.stem


def build_spawn_plan(
    brief_paths: Iterable[Path],
    *,
    phase: str,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
) -> List[Dict[str, Any]]:
    """Build manual subagent spawn instructions without claiming execution."""

    plan = []
    for path in brief_paths:
        route = route_role(role_from_brief_path(path), phase=phase, critic_depth=critic_depth, agent_budget=agent_budget)
        route["brief_path"] = str(path)
        route["instruction"] = "Spawn manually only when the main agent decides the token cost is justified."
        plan.append(route)
    return plan


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Build RDD custom-agent spawn plan.")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--critic-depth", choices=["minimal", "standard", "deep"], default="standard")
    parser.add_argument("--agent-budget", choices=["spark-first", "balanced", "deep"], default="spark-first")
    parser.add_argument("--brief", action="append", default=[])
    parser.add_argument("--role", action="append", default=[])
    args = parser.parse_args()

    if args.brief:
        result: Any = build_spawn_plan(
            [Path(item) for item in args.brief],
            phase=args.phase,
            critic_depth=args.critic_depth,
            agent_budget=args.agent_budget,
        )
    else:
        result = [
            route_role(role, phase=args.phase, critic_depth=args.critic_depth, agent_budget=args.agent_budget)
            for role in args.role
        ]
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
