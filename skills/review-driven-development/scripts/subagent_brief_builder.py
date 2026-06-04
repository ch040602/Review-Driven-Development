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

STATE_DIR = Path(".codex") / "review-driven-development"


@dataclass(frozen=True)
class RoleSpec:
    """Definition of one critical-only subagent role."""
    name: str
    phase: str
    focus: str
    required_evidence: str


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
}

ROLE_SETS: Dict[str, List[str]] = {
    "preplan": ["requirements-critic", "language-runtime-critic", "architecture-critic", "existing-code-reuse-refactor-critic", "source-grounding-critic", "markdown-doc-context-critic", "test-tdd-critic", "security-risk-critic", "documentation-critic", "data-csv-critic"],
    "validation": ["validation-runner-critic", "test-tdd-critic", "security-risk-critic", "documentation-critic", "maintainability-critic"],
    "improvement": ["quality-critic", "performance-efficiency-critic", "accuracy-evaluation-critic", "data-csv-critic", "documentation-critic", "maintainability-critic"],
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


def role_list_for_phase(phase: str, inventory: Optional[Mapping[str, Any]] = None) -> List[str]:
    """Return critic roles for a phase using inventory hints."""
    if phase not in ROLE_SETS:
        raise ValueError(f"Unknown phase: {phase}. Expected one of {sorted(ROLE_SETS)}")
    roles = list(ROLE_SETS[phase])
    if inventory and not inventory.get("requires_data_critic", False):
        roles = [role for role in roles if role != "data-csv-critic"]
    if inventory and not inventory.get("has_existing_code", True):
        roles = ["greenfield-scope-critic" if role == "existing-code-reuse-refactor-critic" else role for role in roles]
    if inventory and inventory.get("frameworks") and phase == "preplan":
        roles.append("source-driven-framework-critic")
    return list(dict.fromkeys(roles))


def build_brief(role: str, phase: str, todo_id: str | None, context_summary: str, inventory: Optional[Mapping[str, Any]] = None) -> str:
    """Build a Markdown prompt for one critical-only subagent."""
    spec = get_role_spec(role, phase)
    inventory_note = ""
    if inventory:
        inventory_note = "\n## Inventory hints\n\n" + json.dumps({
            "primary_languages": inventory.get("primary_languages", []),
            "frameworks": inventory.get("frameworks", []),
            "has_existing_code": inventory.get("has_existing_code"),
            "has_tests": inventory.get("has_tests"),
            "requires_data_critic": inventory.get("requires_data_critic"),
        }, ensure_ascii=False, indent=2) + "\n"
    return f"""# Subagent brief: {role}

## Phase

{phase}

## TODO

{todo_id or "N/A"}

## Contract

{CRITICAL_CONTRACT}

## Role-specific focus

{spec.focus}

## Required evidence to inspect

{spec.required_evidence}

## Context summary

{context_summary or "No context summary provided. Inspect available project state and task context."}
{inventory_note}
## Output format

{FINDING_FORMAT}
"""


def write_briefs(root: Path, phase: str, todo_id: str | None, context_summary: str, roles: Optional[Iterable[str]] = None) -> List[Path]:
    """Write critical-only briefs for one phase."""
    inventory = load_inventory(root)
    selected_roles = list(roles) if roles is not None else role_list_for_phase(phase, inventory)
    directory = root / STATE_DIR / "subagent-briefs" / f"{phase}-{now_stamp()}"
    directory.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for role in selected_roles:
        path = directory / f"{role}.md"
        path.write_text(build_brief(role, phase, todo_id, context_summary, inventory), encoding="utf-8")
        paths.append(path)
    return paths


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
    args = parser.parse_args()
    paths = write_briefs(Path(args.root).resolve(), args.phase, args.todo_id, args.context_summary, roles=args.role)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
