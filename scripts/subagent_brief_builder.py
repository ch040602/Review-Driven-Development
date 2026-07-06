#!/usr/bin/env python3
"""
Subagent brief builder for review-driven-development.

Role:
- Generate critical-only briefs for parallel subagents.
- Keep each subagent focused on one role.
- Make main-agent decision authority explicit.
- Produce debate/validation/improvement templates without launching agents.

Implementation notes:
- Role selection uses context inventory hints.
- Briefs preserve the critical-only contract and main-agent decision boundary.
- Structured finding parsing is intentionally conservative; raw findings still
  require main-agent classification.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

try:
    from .model_router import build_spawn_plan, route_role
except ImportError:  # pragma: no cover
    from model_router import build_spawn_plan, route_role  # type: ignore

STATE_DIR = Path(".codex") / "review-driven-development"


@dataclass(frozen=True)
class RoleSpec:
    """Definition of one critical-only subagent role."""
    name: str
    phase: str
    focus: str
    required_evidence: str


@dataclass(frozen=True)
class AgentAllocation:
    """Recommended intelligence tier for a critical-only subagent."""
    tier: str
    reason: str
    escalate_when: str


ROLE_SPECS: Dict[str, RoleSpec] = {
    "requirements-critic": RoleSpec("requirements-critic", "preplan", "Ambiguous, conflicting, missing, or unverifiable requirements.", "Requirement text, source files, docs, user answers."),
    "language-runtime-critic": RoleSpec("language-runtime-critic", "preplan", "Language/runtime tradeoffs, ecosystem fit, deployment constraints.", "Detected languages, build files, user constraints."),
    "architecture-critic": RoleSpec("architecture-critic", "preplan", "Architecture risks, boundaries, state, dependencies, migration impact.", "Repository map, diagrams if available, public interfaces."),
    "existing-code-reuse-refactor-critic": RoleSpec("existing-code-reuse-refactor-critic", "preplan", "Reuse/refactor/rewrite tradeoffs and hidden coupling.", "Existing code, tests, changelog, dependency graph."),
    "greenfield-scope-critic": RoleSpec("greenfield-scope-critic", "preplan", "Overbuilding, missing foundation, invalid assumptions in new code.", "Requirements and target environment."),
    "source-grounding-critic": RoleSpec("source-grounding-critic", "preplan", "Unsupported API/framework assumptions, missing official sources, and stale dependency claims.", "Official docs links, package versions, source snippets, external-skill policy."),
    "markdown-doc-context-critic": RoleSpec("markdown-doc-context-critic", "preplan", "Whether AGENTS.md, README, docs, Markdown specs, and attached text were actually read and reflected.", "AGENTS.md, README files, docs, requirement packet citations."),
    "source-driven-framework-critic": RoleSpec("source-driven-framework-critic", "preplan", "Whether framework decisions are grounded in official docs/source evidence.", "Official docs links, package versions, source snippets."),
    "test-tdd-critic": RoleSpec("test-tdd-critic", "preplan", "Acceptance criteria, failing tests, regression protection.", "Test tree, coverage/eval artifacts, quality-gate commands."),
    "security-risk-critic": RoleSpec("security-risk-critic", "preplan", "Security, privacy, secrets, auth, data handling, destructive operations.", "Trust boundaries, config, env usage, data files."),
    "documentation-critic": RoleSpec("documentation-critic", "preplan", "Docs that must change and docs likely to become stale.", "README, docs, API references, ADRs."),
    "data-csv-critic": RoleSpec("data-csv-critic", "preplan", "CSV/log/data quality, schema, leakage, analysis correctness.", "Data file list, schema sample, analysis/eval scripts."),
    "validation-runner-critic": RoleSpec("validation-runner-critic", "validation", "Whether validation proves the TODO acceptance criteria.", "Diff, TODO criteria, quality-gate output."),
    "maintainability-critic": RoleSpec("maintainability-critic", "validation", "Complexity, naming, coupling, future maintenance burden.", "Touched files, public interfaces, tests."),
    "quality-critic": RoleSpec("quality-critic", "improvement", "Unresolved quality gaps after TODO completion.", "Diff, review findings, validation report."),
    "performance-efficiency-critic": RoleSpec("performance-efficiency-critic", "improvement", "Performance, cost, memory, latency, algorithmic inefficiency.", "Benchmarks, code paths, data sizes, runtime constraints."),
    "accuracy-evaluation-critic": RoleSpec("accuracy-evaluation-critic", "improvement", "Correctness, eval coverage, numerical or LLM response quality.", "Test/eval results, examples, expected outputs."),
    "simplification-critic": RoleSpec("simplification-critic", "validation", "Unnecessary code, dependencies, wrappers, config, abstractions, and future-proofing outside the current TODO.", "Diff, touched files, dependency changes, minimality packet, validation evidence."),
}

ROLE_SETS: Dict[str, List[str]] = {
    "preplan": ["requirements-critic", "language-runtime-critic", "architecture-critic", "existing-code-reuse-refactor-critic", "source-grounding-critic", "markdown-doc-context-critic", "test-tdd-critic", "security-risk-critic", "documentation-critic", "data-csv-critic"],
    "validation": ["validation-runner-critic", "test-tdd-critic", "security-risk-critic", "documentation-critic", "maintainability-critic", "simplification-critic"],
    "improvement": ["quality-critic", "performance-efficiency-critic", "accuracy-evaluation-critic", "data-csv-critic", "documentation-critic", "maintainability-critic", "simplification-critic"],
}
CRITIC_DEPTH_LIMITS = {
    "minimal": 2,
    "standard": 4,
    "deep": 99,
}
AGENT_BUDGETS = {
    "spark-first": "Prefer codex-spark for frequent structured checks; escalate only on concrete risk signals.",
    "balanced": "Use codex-spark for narrow checks, codex-standard for cross-file or uncertain reasoning, and codex-deep for high-risk roles.",
    "deep": "Prefer stronger subagents for broad or high-risk reviews while still allowing codex-spark for mechanical docs/tests checks.",
}
SPARK_FRIENDLY_ROLES = {
    "requirements-critic",
    "test-tdd-critic",
    "documentation-critic",
    "markdown-doc-context-critic",
    "validation-runner-critic",
    "maintainability-critic",
    "quality-critic",
    "greenfield-scope-critic",
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
DEEP_RISK_ROLES = {
    "architecture-critic",
    "security-risk-critic",
    "data-csv-critic",
}

CRITICAL_CONTRACT = """You are a critical-only subagent for review-driven-development.
Do not praise. Do not decide. Do not implement patches.
Find risks, missing evidence, contradictions, regressions, inefficiencies, and weak assumptions.
Return structured findings only. The main agent decides whether to accept, reject, defer, or ask the user.
"""

FINDING_FORMAT = """Return findings in this format:

```yaml
- finding_id: RDD-{ROLE}-001
  severity: blocker | high | medium | low
  area: requirements | architecture | language | reuse | tests | security | docs | data | performance | accuracy | maintainability | source
  claim: ""
  risk: ""
  missing_evidence: ""
  recommendation: ""
  check: ""
```
"""


def now_stamp() -> str:
    """Return timestamp for brief directory names."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def get_role_spec(role: str, phase: str) -> RoleSpec:
    """Return a role spec, with a generic fallback."""
    return ROLE_SPECS.get(role, RoleSpec(role, phase, f"Critical review for {role}.", "Available task context and state files."))


def load_inventory(root: Path) -> Dict[str, Any] | None:
    """Load saved context inventory if present."""
    path = root / STATE_DIR / "context-inventory.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def role_list_for_phase(
    phase: str,
    inventory: Optional[Mapping[str, Any]] = None,
    *,
    critic_depth: str = "standard",
    max_roles: int | None = None,
) -> List[str]:
    """Return critic roles for a phase using inventory hints and depth caps."""

    if phase not in ROLE_SETS:
        raise ValueError(f"Unknown phase: {phase}. Expected one of {sorted(ROLE_SETS)}")
    if critic_depth not in CRITIC_DEPTH_LIMITS:
        raise ValueError(f"Unknown critic depth: {critic_depth}. Expected one of {sorted(CRITIC_DEPTH_LIMITS)}")

    if inventory and isinstance(inventory.get("recommended_critics"), list) and phase == "preplan":
        roles = [str(role) for role in inventory.get("recommended_critics", [])]
    elif phase == "preplan":
        roles = ["requirements-critic", "test-tdd-critic"]
        roles.append("existing-code-reuse-refactor-critic" if not inventory or inventory.get("has_existing_code", True) else "greenfield-scope-critic")
    elif phase == "validation":
        roles = ["validation-runner-critic", "test-tdd-critic", "maintainability-critic", "simplification-critic"]
    else:
        roles = ["quality-critic", "performance-efficiency-critic", "accuracy-evaluation-critic"]

    if inventory:
        if inventory.get("requires_data_critic"):
            roles.append("data-csv-critic")
        if inventory.get("needs_security_critic"):
            roles.append("security-risk-critic")
        if inventory.get("frameworks") and phase == "preplan":
            roles.append("source-driven-framework-critic")
        if inventory.get("docs") and phase in {"validation", "improvement"}:
            roles.append("documentation-critic")

    if inventory and not inventory.get("requires_data_critic", False):
        roles = [role for role in roles if role != "data-csv-critic"]
    if inventory and not inventory.get("needs_security_critic", False):
        roles = [role for role in roles if role != "security-risk-critic"]
    if inventory and not inventory.get("frameworks") and phase == "preplan":
        roles = [role for role in roles if role not in {"source-driven-framework-critic", "source-grounding-critic"}]
    if inventory and not inventory.get("docs") and phase in {"preplan", "validation", "improvement"}:
        roles = [role for role in roles if role not in {"documentation-critic", "markdown-doc-context-critic"}]
    if inventory and not inventory.get("has_existing_code", True):
        roles = ["greenfield-scope-critic" if role == "existing-code-reuse-refactor-critic" else role for role in roles]

    roles = list(dict.fromkeys(roles))
    cap = max_roles if max_roles is not None else CRITIC_DEPTH_LIMITS[critic_depth]
    return roles[:max(1, cap)]


def agent_allocation_for_role(
    role: str,
    phase: str,
    inventory: Optional[Mapping[str, Any]] = None,
    *,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
) -> AgentAllocation:
    """Choose a subagent intelligence tier from role and risk signals.

    The returned tier is a routing hint for the main agent or external
    orchestrator. It does not launch agents and does not weaken the critical-only
    contract.
    """

    if critic_depth not in CRITIC_DEPTH_LIMITS:
        raise ValueError(f"Unknown critic depth: {critic_depth}. Expected one of {sorted(CRITIC_DEPTH_LIMITS)}")
    if agent_budget not in AGENT_BUDGETS:
        raise ValueError(f"Unknown agent budget: {agent_budget}. Expected one of {sorted(AGENT_BUDGETS)}")

    has_security_signal = bool(inventory and inventory.get("needs_security_critic"))
    has_data_signal = bool(inventory and inventory.get("requires_data_critic"))
    high_risk_role = role in DEEP_RISK_ROLES
    broad_reasoning_role = role in STANDARD_ROLES or role == "architecture-critic"
    structured_role = role in SPARK_FRIENDLY_ROLES

    if agent_budget == "deep":
        if high_risk_role or critic_depth == "deep":
            return AgentAllocation(
                "codex-deep",
                "deep budget or high-risk role requires stronger cross-file reasoning",
                "Already escalated; reduce only after evidence proves the risk is local and mechanical.",
            )
        if structured_role:
            return AgentAllocation(
                "codex-spark",
                "structured checklist role remains cheap even in deep budget",
                "Escalate if it reports ambiguity, missing evidence, or cross-module coupling.",
            )
        return AgentAllocation(
            "codex-standard",
            "deep budget keeps non-mechanical reasoning above spark",
            "Escalate to codex-deep if blocker/high uncertainty remains after the first pass.",
        )

    if agent_budget == "balanced":
        if high_risk_role and (critic_depth == "deep" or has_security_signal or has_data_signal):
            return AgentAllocation(
                "codex-deep",
                "balanced budget escalates concrete security/data/architecture risk",
                "Reduce only when the inventory signal is false positive.",
            )
        if structured_role:
            return AgentAllocation(
                "codex-spark",
                "structured local checklist can run frequently at low cost",
                "Escalate if the checklist finds unresolved high-risk ambiguity.",
            )
        return AgentAllocation(
            "codex-standard",
            "balanced budget uses standard reasoning for non-mechanical review",
            "Escalate to codex-deep for broad migration, security, data, or architecture blockers.",
        )

    # spark-first
    if high_risk_role and critic_depth == "deep":
        return AgentAllocation(
            "codex-deep",
            "deep critic depth overrides spark-first for high-risk roles",
            "Drop to codex-standard only if the main agent records a narrower risk boundary.",
        )
    if high_risk_role or broad_reasoning_role:
        return AgentAllocation(
            "codex-standard",
            "role or inventory signal needs more reasoning than a frequent checklist pass",
            "Escalate to codex-deep if security/data/architecture risk remains unresolved.",
        )
    return AgentAllocation(
        "codex-spark",
        "default low-cost tier for frequent structured critical checks",
        "Escalate if findings mention blocker/high severity, unclear requirements, or cross-file coupling.",
    )


def allocation_table_for_roles(
    roles: Iterable[str],
    phase: str,
    inventory: Optional[Mapping[str, Any]] = None,
    *,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
) -> List[Dict[str, str]]:
    """Return routing hints for a role list."""

    rows: List[Dict[str, str]] = []
    for role in roles:
        allocation = agent_allocation_for_role(
            role,
            phase,
            inventory,
            critic_depth=critic_depth,
            agent_budget=agent_budget,
        )
        route = route_role(
            role,
            phase=phase,
            critic_depth=critic_depth,
            agent_budget=agent_budget,
        )
        rows.append({
            "role": role,
            "agent_tier": allocation.tier,
            "custom_agent_name": route["custom_agent_name"],
            "model": route["model"],
            "sandbox": route["sandbox"],
            "reason": allocation.reason,
            "escalate_when": allocation.escalate_when,
            "escalate_to": str(route.get("escalate_to", "")),
        })
    return rows


def compact_context_summary(context_summary: str, max_chars: int) -> str:
    """Bound context embedded in generated briefs."""

    if max_chars <= 0:
        return "[omitted for token budget]"
    compact = context_summary or "No context summary provided. Inspect available project state and task context."
    if len(compact) <= max_chars:
        return compact
    return compact[: max(0, max_chars - 40)].rstrip() + "\n[truncated for token budget]"


def build_brief(
    role: str,
    phase: str,
    todo_id: str | None,
    context_summary: str,
    inventory: Optional[Mapping[str, Any]] = None,
    *,
    context_max_chars: int = 1200,
    critic_depth: str = "standard",
    agent_budget: str = "spark-first",
) -> str:
    """Build a Markdown prompt for one critical-only subagent."""
    spec = get_role_spec(role, phase)
    allocation = agent_allocation_for_role(
        role,
        phase,
        inventory,
        critic_depth=critic_depth,
        agent_budget=agent_budget,
    )
    inventory_note = ""
    if inventory:
        inventory_note = "\n## Inventory hints\n\n" + json.dumps({
            "primary_languages": inventory.get("primary_languages", []),
            "frameworks": inventory.get("frameworks", []),
            "has_existing_code": inventory.get("has_existing_code"),
            "has_tests": inventory.get("has_tests"),
            "requires_data_critic": inventory.get("requires_data_critic"),
            "needs_security_critic": inventory.get("needs_security_critic"),
            "inventory_mode": inventory.get("inventory_mode"),
            "docs": list(inventory.get("docs", []))[:8],
            "tests": list(inventory.get("tests", []))[:8],
            "source_files_sample": list(inventory.get("source_files_sample", []))[:12],
        }, ensure_ascii=False, indent=2) + "\n"
    bounded_context = compact_context_summary(context_summary, context_max_chars)
    return f"""# Subagent brief: {role}

## Phase

{phase}

## TODO

{todo_id or "N/A"}

## Contract

{CRITICAL_CONTRACT}

## Agent allocation hint

- Recommended tier: `{allocation.tier}`
- Custom agent: `{route_role(role, phase=phase, critic_depth=critic_depth, agent_budget=agent_budget)["custom_agent_name"]}`
- Reason: {allocation.reason}
- Escalate when: {allocation.escalate_when}

## Role-specific focus

{spec.focus}

## Required evidence to inspect

{spec.required_evidence}

## Context summary

{bounded_context}
{inventory_note}
## Output format

{FINDING_FORMAT}
"""


def write_briefs(
    root: Path,
    phase: str,
    todo_id: str | None,
    context_summary: str,
    roles: Optional[Iterable[str]] = None,
    *,
    critic_depth: str = "standard",
    max_roles: int | None = None,
    context_max_chars: int = 1200,
    agent_budget: str = "spark-first",
) -> List[Path]:
    """Write critical-only briefs for one phase."""
    if agent_budget not in AGENT_BUDGETS:
        raise ValueError(f"Unknown agent budget: {agent_budget}. Expected one of {sorted(AGENT_BUDGETS)}")
    inventory = load_inventory(root)
    selected_roles = (
        list(roles)
        if roles is not None
        else role_list_for_phase(phase, inventory, critic_depth=critic_depth, max_roles=max_roles)
    )
    directory = root / STATE_DIR / "subagent-briefs" / f"{phase}-{now_stamp()}"
    directory.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for role in selected_roles:
        path = directory / f"{role}.md"
        path.write_text(
            build_brief(
                role,
                phase,
                todo_id,
                context_summary,
                inventory,
                context_max_chars=context_max_chars,
                critic_depth=critic_depth,
                agent_budget=agent_budget,
            ),
            encoding="utf-8",
        )
        paths.append(path)
    return paths


def write_spawn_plan(root: Path, phase: str, brief_paths: Iterable[Path], *, critic_depth: str = "standard", agent_budget: str = "spark-first") -> Path:
    """Write a manual custom-agent spawn plan for generated briefs."""

    plan = build_spawn_plan(brief_paths, phase=phase, critic_depth=critic_depth, agent_budget=agent_budget)
    directory = root / STATE_DIR / "subagent-briefs"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{phase}-spawn-plan-{now_stamp()}.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def parse_findings_placeholder(text: str) -> List[Dict[str, Any]]:
    """Placeholder parser for subagent findings.

    Codex should replace this with YAML/JSON parsing once output format is enforced.
    """
    if not text.strip():
        return []
    return [{
        "finding_id": "RDD-RAW-001",
        "severity": "medium",
        "area": "unknown",
        "claim": text.strip(),
        "risk": "Raw finding needs main-agent classification.",
        "missing_evidence": "Structured parsing not implemented yet.",
        "recommendation": "Parse and classify this finding manually.",
        "check": "Main agent decision recorded in decision-log.md.",
    }]


def build_decision_table(findings: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Create a decision table template for the main agent."""
    rows: List[Dict[str, Any]] = []
    for finding in findings:
        row = dict(finding)
        row.setdefault("decision", "needs_main_agent_decision")
        row.setdefault("decision_reason", "")
        row.setdefault("todo_id", "")
        rows.append(row)
    return rows


def main() -> None:
    """CLI entrypoint for writing critical-only subagent briefs."""

    parser = argparse.ArgumentParser(description="Build critical-only subagent briefs.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--phase", choices=sorted(ROLE_SETS), required=True)
    parser.add_argument("--todo-id")
    parser.add_argument("--context-summary", default="")
    parser.add_argument("--role", action="append", help="Override role list; can be repeated")
    parser.add_argument("--critic-depth", choices=sorted(CRITIC_DEPTH_LIMITS), default="standard")
    parser.add_argument("--max-roles", type=int)
    parser.add_argument("--context-max-chars", type=int, default=1200)
    parser.add_argument("--agent-budget", choices=sorted(AGENT_BUDGETS), default="spark-first")
    parser.add_argument("--emit-agent-instructions", action="store_true", help="Emit allocation metadata for generated briefs")
    parser.add_argument("--emit-spawn-plan", action="store_true", help="Write and emit a manual custom-agent spawn plan")
    parser.add_argument("--emit-agent-files", action="store_true", help="Emit expected .codex/agents config file paths")
    args = parser.parse_args()
    paths = write_briefs(
        Path(args.root).resolve(),
        args.phase,
        args.todo_id,
        args.context_summary,
        roles=args.role,
        critic_depth=args.critic_depth,
        max_roles=args.max_roles,
        context_max_chars=args.context_max_chars,
        agent_budget=args.agent_budget,
    )
    if args.emit_agent_instructions or args.emit_spawn_plan or args.emit_agent_files:
        roles = [path.stem for path in paths]
        payload: Dict[str, Any] = {"brief_paths": [str(path) for path in paths]}
        if args.emit_agent_instructions:
            payload["agent_allocations"] = allocation_table_for_roles(
                roles,
                args.phase,
                load_inventory(Path(args.root).resolve()),
                critic_depth=args.critic_depth,
                agent_budget=args.agent_budget,
            )
        if args.emit_spawn_plan:
            payload["spawn_plan_path"] = str(write_spawn_plan(
                Path(args.root).resolve(),
                args.phase,
                paths,
                critic_depth=args.critic_depth,
                agent_budget=args.agent_budget,
            ))
        if args.emit_agent_files:
            payload["agent_files"] = [
                ".codex/agents/rdd-spark-critic.toml",
                ".codex/agents/rdd-standard-critic.toml",
                ".codex/agents/rdd-deep-critic.toml",
            ]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for path in paths:
            print(path)


if __name__ == "__main__":
    main()
