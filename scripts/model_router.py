#!/usr/bin/env python3
"""Route RDD work from capability, complexity, reasoning, availability, and budget."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "references" / "model-routing-policy.json"


def load_routing_policy(path: Path | str | None = None) -> Dict[str, Any]:
    """Load and validate the data-driven model routing policy."""

    policy_path = Path(path).expanduser().resolve() if path else DEFAULT_POLICY_PATH
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    validate_routing_policy(policy)
    return policy


def _require_order(policy: Mapping[str, Any], key: str) -> List[str]:
    values = policy.get(key)
    if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
        raise ValueError(f"Routing policy {key} must be a non-empty string list")
    if len(values) != len(set(values)):
        raise ValueError(f"Routing policy {key} contains duplicates")
    return list(values)


def validate_routing_policy(policy: Mapping[str, Any]) -> None:
    """Reject incomplete policies before they can silently weaken routing."""

    if policy.get("schema_version") != 1:
        raise ValueError("Routing policy schema_version must be 1")
    complexities = _require_order(policy, "complexity_order")
    efforts = _require_order(policy, "reasoning_effort_order")

    budgets = policy.get("budget_profiles")
    if not isinstance(budgets, Mapping) or not budgets:
        raise ValueError("Routing policy budget_profiles must be a non-empty object")
    for name, raw_budget in budgets.items():
        if not isinstance(raw_budget, Mapping):
            raise ValueError(f"Budget profile {name} must be an object")
        if int(raw_budget.get("max_cost_tier", 0)) < 1:
            raise ValueError(f"Budget profile {name} max_cost_tier must be positive")
        if raw_budget.get("max_reasoning_effort") not in efforts:
            raise ValueError(f"Budget profile {name} has an unknown max_reasoning_effort")
        if int(raw_budget.get("max_fallbacks", -1)) < 0:
            raise ValueError(f"Budget profile {name} max_fallbacks must be non-negative")
        if int(raw_budget.get("max_plan_cost_units", 0)) < 1:
            raise ValueError(f"Budget profile {name} max_plan_cost_units must be positive")

    task_profiles = policy.get("task_profiles")
    if not isinstance(task_profiles, Mapping) or not task_profiles:
        raise ValueError("Routing policy task_profiles must be a non-empty object")
    for name, raw_profile in task_profiles.items():
        if not isinstance(raw_profile, Mapping):
            raise ValueError(f"Task profile {name} must be an object")
        capabilities = raw_profile.get("required_capabilities")
        if (
            not isinstance(capabilities, list)
            or not capabilities
            or any(not isinstance(capability, str) or not capability for capability in capabilities)
        ):
            raise ValueError(f"Task profile {name} must declare required_capabilities")
        if raw_profile.get("contract") not in {"implementation", "critical-only"}:
            raise ValueError(f"Task profile {name} has an unknown contract")
        if not isinstance(raw_profile.get("sandbox"), str) or not raw_profile.get("sandbox"):
            raise ValueError(f"Task profile {name} must declare a sandbox")
        if raw_profile.get("complexity") not in complexities:
            raise ValueError(f"Task profile {name} has an unknown complexity")
        if raw_profile.get("reasoning_effort") not in efforts:
            raise ValueError(f"Task profile {name} has an unknown reasoning_effort")
        for depth, override in dict(raw_profile.get("depth_overrides", {})).items():
            if depth not in {"minimal", "standard", "deep"} or not isinstance(override, Mapping):
                raise ValueError(f"Task profile {name} has an invalid depth override")
            if "complexity" in override and override["complexity"] not in complexities:
                raise ValueError(f"Task profile {name} depth {depth} has an unknown complexity")
            if "reasoning_effort" in override and override["reasoning_effort"] not in efforts:
                raise ValueError(f"Task profile {name} depth {depth} has an unknown reasoning_effort")

    default_task_kind = policy.get("default_role_task_kind")
    if default_task_kind not in task_profiles:
        raise ValueError("Routing policy default_role_task_kind must name a task profile")
    for role, task_kind in dict(policy.get("role_task_kinds", {})).items():
        if not role or task_kind not in task_profiles:
            raise ValueError(f"Role mapping {role!r} points to an unknown task profile")

    models = policy.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("Routing policy models must be a non-empty list")
    model_ids: List[str] = []
    for raw_model in models:
        if not isinstance(raw_model, Mapping):
            raise ValueError("Each routing model must be an object")
        model_id = raw_model.get("id")
        if not isinstance(model_id, str) or not model_id:
            raise ValueError("Each routing model must have a non-empty id")
        model_ids.append(model_id)
        capabilities = raw_model.get("capabilities")
        if (
            not isinstance(capabilities, list)
            or not capabilities
            or any(not isinstance(capability, str) or not capability for capability in capabilities)
        ):
            raise ValueError(f"Model {model_id} must declare capabilities")
        if raw_model.get("max_complexity") not in complexities:
            raise ValueError(f"Model {model_id} has an unknown max_complexity")
        supported_efforts = raw_model.get("reasoning_efforts")
        if not isinstance(supported_efforts, list) or not supported_efforts:
            raise ValueError(f"Model {model_id} must declare reasoning_efforts")
        if any(effort not in efforts for effort in supported_efforts):
            raise ValueError(f"Model {model_id} has an unknown reasoning effort")
        if int(raw_model.get("cost_tier", 0)) < 1:
            raise ValueError(f"Model {model_id} cost_tier must be positive")
        for field in ("agent_tiers", "critic_agents"):
            effort_map = raw_model.get(field, {})
            if not isinstance(effort_map, Mapping):
                raise ValueError(f"Model {model_id} {field} must be an object")
            for effort, value in effort_map.items():
                if effort not in supported_efforts:
                    raise ValueError(f"Model {model_id} {field} maps unsupported effort {effort}")
                if not isinstance(value, str) or not value:
                    raise ValueError(f"Model {model_id} {field}.{effort} must be a non-empty string")
    if len(model_ids) != len(set(model_ids)):
        raise ValueError("Routing policy model ids must be unique")


def _policy_or_default(routing_policy: Mapping[str, Any] | None) -> Mapping[str, Any]:
    policy = routing_policy if routing_policy is not None else load_routing_policy()
    validate_routing_policy(policy)
    return policy


def _rank(order: Sequence[str], value: str, field: str) -> int:
    try:
        return order.index(value)
    except ValueError as exc:
        raise ValueError(f"Unknown {field}: {value}. Expected one of {list(order)}") from exc


def _resolve_budget(
    policy: Mapping[str, Any],
    agent_budget: str,
    *,
    max_cost_tier: int | None = None,
    max_reasoning_effort: str | None = None,
    max_fallbacks: int | None = None,
    max_plan_cost_units: int | None = None,
) -> Dict[str, Any]:
    profiles = policy["budget_profiles"]
    if agent_budget not in profiles:
        raise ValueError(f"Unknown agent budget: {agent_budget}. Expected one of {sorted(profiles)}")
    budget = dict(profiles[agent_budget])
    if max_cost_tier is not None:
        if max_cost_tier < 1:
            raise ValueError("max_cost_tier must be positive")
        budget["max_cost_tier"] = max_cost_tier
    if max_reasoning_effort is not None:
        _rank(policy["reasoning_effort_order"], max_reasoning_effort, "reasoning effort")
        budget["max_reasoning_effort"] = max_reasoning_effort
    if max_fallbacks is not None:
        if max_fallbacks < 0:
            raise ValueError("max_fallbacks must be non-negative")
        budget["max_fallbacks"] = max_fallbacks
    if max_plan_cost_units is not None:
        if max_plan_cost_units < 0:
            raise ValueError("max_plan_cost_units must be non-negative")
        budget["max_plan_cost_units"] = max_plan_cost_units
    budget["profile"] = agent_budget
    return budget


def _resolve_task_profile(
    policy: Mapping[str, Any],
    task_kind: str,
    *,
    critic_depth: str,
    complexity: str | None,
    reasoning_effort: str | None,
) -> Dict[str, Any]:
    task_profiles = policy["task_profiles"]
    if task_kind not in task_profiles:
        raise ValueError(f"Unknown task kind: {task_kind}. Expected one of {sorted(task_profiles)}")
    if critic_depth not in {"minimal", "standard", "deep"}:
        raise ValueError("critic_depth must be minimal, standard, or deep")
    profile = dict(task_profiles[task_kind])
    profile.pop("depth_overrides", None)
    profile.update(dict(task_profiles[task_kind].get("depth_overrides", {}).get(critic_depth, {})))
    if complexity is not None:
        _rank(policy["complexity_order"], complexity, "complexity")
        profile["complexity"] = complexity
    if reasoning_effort is not None:
        _rank(policy["reasoning_effort_order"], reasoning_effort, "reasoning effort")
        profile["reasoning_effort"] = reasoning_effort
    return profile


def _model_effort(
    model: Mapping[str, Any],
    required_effort: str,
    max_effort: str,
    effort_order: Sequence[str],
) -> str | None:
    required_rank = _rank(effort_order, required_effort, "reasoning effort")
    max_rank = _rank(effort_order, max_effort, "reasoning effort")
    eligible = [
        effort
        for effort in model["reasoning_efforts"]
        if required_rank <= _rank(effort_order, effort, "reasoning effort") <= max_rank
    ]
    return min(eligible, key=lambda effort: _rank(effort_order, effort, "reasoning effort"), default=None)


def _supports_requirements(
    model: Mapping[str, Any],
    required_capabilities: set[str],
    complexity: str,
    complexity_order: Sequence[str],
) -> bool:
    return required_capabilities.issubset(set(model["capabilities"])) and _rank(
        complexity_order, str(model["max_complexity"]), "complexity"
    ) >= _rank(complexity_order, complexity, "complexity")


def _candidate_record(
    model: Mapping[str, Any],
    effort: str,
    contract: str,
    effort_order: Sequence[str],
) -> Dict[str, Any]:
    custom_agent = ""
    if contract == "critical-only":
        custom_agent = str(dict(model.get("critic_agents", {})).get(effort, ""))
    agent_tier = str(dict(model.get("agent_tiers", {})).get(effort, ""))
    cost_units = int(model["cost_tier"]) * (_rank(effort_order, effort, "reasoning effort") + 1)
    return {
        "agent_tier": agent_tier,
        "custom_agent_name": custom_agent,
        "estimated_cost_units": cost_units,
        "model": str(model["id"]),
        "reasoning_effort": effort,
    }


def route_task(
    task_kind: str,
    *,
    phase: str,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
    complexity: str | None = None,
    reasoning_effort: str | None = None,
    available_models: Iterable[str] | None = None,
    routing_policy: Mapping[str, Any] | None = None,
    max_cost_tier: int | None = None,
    max_reasoning_effort: str | None = None,
    max_fallbacks: int | None = None,
) -> Dict[str, Any]:
    """Select the least-cost available model that satisfies all hard requirements."""

    policy = _policy_or_default(routing_policy)
    profile = _resolve_task_profile(
        policy,
        task_kind,
        critic_depth=critic_depth,
        complexity=complexity,
        reasoning_effort=reasoning_effort,
    )
    budget = _resolve_budget(
        policy,
        agent_budget,
        max_cost_tier=max_cost_tier,
        max_reasoning_effort=max_reasoning_effort,
        max_fallbacks=max_fallbacks,
    )
    complexity_order = policy["complexity_order"]
    effort_order = policy["reasoning_effort_order"]
    required_capabilities = set(str(item) for item in profile["required_capabilities"])
    required_complexity = str(profile["complexity"])
    required_effort = str(profile["reasoning_effort"])
    models = list(policy["models"])

    if available_models is None:
        available_ids = {str(model["id"]) for model in models if model.get("available_by_default", False)}
        availability_source = "catalog-default"
    else:
        available_ids = {str(model_id) for model_id in available_models}
        availability_source = "explicit"

    capable_models = [
        model
        for model in models
        if _supports_requirements(model, required_capabilities, required_complexity, complexity_order)
        and _model_effort(model, required_effort, effort_order[-1], effort_order) is not None
    ]
    available_capable_models = [model for model in capable_models if str(model["id"]) in available_ids]
    candidates: List[tuple[Mapping[str, Any], str]] = []
    for model in available_capable_models:
        effort = _model_effort(model, required_effort, str(budget["max_reasoning_effort"]), effort_order)
        if effort is not None and int(model["cost_tier"]) <= int(budget["max_cost_tier"]):
            candidates.append((model, effort))

    candidates.sort(
        key=lambda item: (
            int(item[0]["cost_tier"]),
            int(item[0].get("latency_tier", item[0]["cost_tier"])),
            _rank(complexity_order, str(item[0]["max_complexity"]), "complexity")
            - _rank(complexity_order, required_complexity, "complexity"),
            -int(item[0].get("quality_tier", 0)),
            str(item[0]["id"]),
        )
    )

    if candidates:
        route_status = "selected"
    elif not capable_models:
        route_status = "unsupported"
    elif not available_capable_models:
        route_status = "unavailable"
    else:
        route_status = "budget_limited"

    base: Dict[str, Any] = {
        "route_status": route_status,
        "phase": phase,
        "task_kind": task_kind,
        "contract": str(profile["contract"]),
        "required_capabilities": sorted(required_capabilities),
        "complexity": required_complexity,
        "required_reasoning_effort": required_effort,
        "availability_source": availability_source,
        "available_models": sorted(available_ids),
        "budget": budget,
        "sandbox": str(profile["sandbox"]),
        "escalate_to": str(profile.get("escalate_to_task_kind", "")),
        "escalate_when": list(profile.get("escalate_when", [])),
        "fallback_action": str(policy["fallback_action"]),
        "model": "",
        "reasoning_effort": "",
        "agent_tier": "",
        "custom_agent_name": "",
        "estimated_cost_units": 0,
        "fallbacks": [],
    }
    if not candidates:
        return base

    selected_model, selected_effort = candidates[0]
    selected = _candidate_record(selected_model, selected_effort, str(profile["contract"]), effort_order)
    base.update(selected)
    fallback_limit = int(budget["max_fallbacks"])
    base["fallbacks"] = [
        _candidate_record(model, effort, str(profile["contract"]), effort_order)
        for model, effort in candidates[1 : 1 + fallback_limit]
    ]
    base["selection_reason"] = (
        "Selected the lowest-cost/latency available model satisfying the required capabilities, "
        "complexity, reasoning floor, and budget ceiling."
    )
    return base


def route_role(
    role: str,
    *,
    phase: str,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
    complexity: str | None = None,
    reasoning_effort: str | None = None,
    available_models: Iterable[str] | None = None,
    routing_policy: Mapping[str, Any] | None = None,
    max_cost_tier: int | None = None,
    max_reasoning_effort: str | None = None,
    max_fallbacks: int | None = None,
) -> Dict[str, Any]:
    """Route one critical-only role through its policy task profile."""

    policy = _policy_or_default(routing_policy)
    task_kind = str(dict(policy.get("role_task_kinds", {})).get(role, policy["default_role_task_kind"]))
    route = route_task(
        task_kind,
        phase=phase,
        critic_depth=critic_depth,
        agent_budget=agent_budget,
        complexity=complexity,
        reasoning_effort=reasoning_effort,
        available_models=available_models,
        routing_policy=policy,
        max_cost_tier=max_cost_tier,
        max_reasoning_effort=max_reasoning_effort,
        max_fallbacks=max_fallbacks,
    )
    route["role"] = role
    return route


def role_from_brief_path(path: Path) -> str:
    """Infer role from a generated brief path."""

    return path.stem


def build_spawn_plan(
    brief_paths: Iterable[Path],
    *,
    phase: str,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
    complexity: str | None = None,
    reasoning_effort: str | None = None,
    available_models: Iterable[str] | None = None,
    routing_policy: Mapping[str, Any] | None = None,
    max_cost_tier: int | None = None,
    max_reasoning_effort: str | None = None,
    max_fallbacks: int | None = None,
    max_plan_cost_units: int | None = None,
) -> List[Dict[str, Any]]:
    """Build a budget-bounded manual spawn plan without claiming execution."""

    policy = _policy_or_default(routing_policy)
    budget = _resolve_budget(
        policy,
        agent_budget,
        max_cost_tier=max_cost_tier,
        max_reasoning_effort=max_reasoning_effort,
        max_fallbacks=max_fallbacks,
        max_plan_cost_units=max_plan_cost_units,
    )
    limit = int(budget["max_plan_cost_units"])
    spent = 0
    plan: List[Dict[str, Any]] = []
    for path in brief_paths:
        route = route_role(
            role_from_brief_path(path),
            phase=phase,
            critic_depth=critic_depth,
            agent_budget=agent_budget,
            complexity=complexity,
            reasoning_effort=reasoning_effort,
            available_models=available_models,
            routing_policy=policy,
            max_cost_tier=max_cost_tier,
            max_reasoning_effort=max_reasoning_effort,
            max_fallbacks=max_fallbacks,
        )
        route["budget"]["max_plan_cost_units"] = limit
        spent_before = spent
        estimated = int(route["estimated_cost_units"])
        if route["route_status"] == "selected" and spent + estimated > limit:
            route["blocked_model"] = route["model"]
            route["blocked_reasoning_effort"] = route["reasoning_effort"]
            route["route_status"] = "plan_budget_exceeded"
            route["model"] = ""
            route["reasoning_effort"] = ""
            route["agent_tier"] = ""
            route["custom_agent_name"] = ""
            route["estimated_cost_units"] = 0
            route["fallbacks"] = []
            route["selection_reason"] = "Candidate satisfies the route but exceeds the aggregate plan budget."
        elif route["route_status"] == "selected":
            spent += estimated
        route["plan_budget"] = {
            "limit": limit,
            "spent_before": spent_before,
            "spent_after": spent,
            "remaining": max(0, limit - spent),
        }
        route["brief_path"] = str(path)
        route["instruction"] = (
            "Spawn manually only when the main agent decides the token cost is justified."
            if route["route_status"] == "selected"
            else f"Do not spawn this route. {route['fallback_action']}"
        )
        plan.append(route)
    return plan


def _model_list(policy: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "id": model["id"],
            "available_by_default": bool(model.get("available_by_default", False)),
            "capabilities": model["capabilities"],
            "max_complexity": model["max_complexity"],
            "reasoning_efforts": model["reasoning_efforts"],
            "cost_tier": model["cost_tier"],
        }
        for model in policy["models"]
    ]


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Build capability-based RDD model and spawn routes.")
    parser.add_argument("--phase")
    parser.add_argument("--critic-depth", choices=["minimal", "standard", "deep"], default="standard")
    parser.add_argument("--agent-budget", default="spark-first")
    parser.add_argument("--brief", action="append", default=[])
    parser.add_argument("--role", action="append", default=[])
    parser.add_argument("--task-kind")
    parser.add_argument("--complexity")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--available-model", action="append")
    parser.add_argument("--routing-policy")
    parser.add_argument("--max-cost-tier", type=int)
    parser.add_argument("--max-reasoning-effort")
    parser.add_argument("--max-fallbacks", type=int)
    parser.add_argument("--max-plan-cost-units", type=int)
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args()

    policy = load_routing_policy(args.routing_policy)
    if args.list_models:
        result: Any = _model_list(policy)
    else:
        if not args.phase:
            parser.error("--phase is required unless --list-models is used")
        common = {
            "phase": args.phase,
            "critic_depth": args.critic_depth,
            "agent_budget": args.agent_budget,
            "complexity": args.complexity,
            "reasoning_effort": args.reasoning_effort,
            "available_models": args.available_model,
            "routing_policy": policy,
            "max_cost_tier": args.max_cost_tier,
            "max_reasoning_effort": args.max_reasoning_effort,
            "max_fallbacks": args.max_fallbacks,
        }
        if args.brief:
            result = build_spawn_plan(
                [Path(item) for item in args.brief],
                max_plan_cost_units=args.max_plan_cost_units,
                **common,
            )
        elif args.role:
            result = [route_role(role, **common) for role in args.role]
        elif args.task_kind:
            result = route_task(args.task_kind, **common)
        else:
            parser.error("provide --brief, --role, --task-kind, or --list-models")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
