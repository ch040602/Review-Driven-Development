#!/usr/bin/env python3
"""High-level workflow orchestration preview.

This script does not replace the Codex main agent. It provides a stable function
map that Codex can call while executing the skill.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Mapping, Optional

try:
    from .context_inventory import build_inventory, save_inventory
    from .critic_ledger import accepted_findings, findings_to_todo_seeds
    from .doc_sync_check import build_doc_sync_report, save_report as save_doc_report
    from .quality_gate import build_report, load_commands, save_report, select_commands
    from .rdd_state import ensure_state, load_defaults
    from .requirement_analyzer import create_requirement_packet, packet_to_dict
    from .subagent_brief_builder import write_briefs
    from .todo_manager import create_todo, start_next_todo
except ImportError:  # pragma: no cover
    from context_inventory import build_inventory, save_inventory  # type: ignore
    from critic_ledger import accepted_findings, findings_to_todo_seeds  # type: ignore
    from doc_sync_check import build_doc_sync_report, save_report as save_doc_report  # type: ignore
    from quality_gate import build_report, load_commands, save_report, select_commands  # type: ignore
    from rdd_state import ensure_state, load_defaults  # type: ignore
    from requirement_analyzer import create_requirement_packet, packet_to_dict  # type: ignore
    from subagent_brief_builder import write_briefs  # type: ignore
    from todo_manager import create_todo, start_next_todo  # type: ignore


def run_context_phase(root: Path, prompt: str) -> Dict[str, object]:
    """Inventory project context and build a requirement packet."""

    ensure_state(root)
    context = build_inventory(root)
    inventory_path = save_inventory(root, context)
    packet = create_requirement_packet(prompt, root, saved_inventory=True)
    return {"context_inventory": context, "inventory_path": str(inventory_path), "requirement_packet": packet_to_dict(packet)}


def needs_first_run(root: Path) -> bool:
    """Return True when defaults are missing."""

    return load_defaults(root) is None


def build_first_run_action(root: Path, prompt: str) -> Dict[str, object]:
    """Return the action the main agent should take for first-run setup.

    This function does not ask the user by itself. Codex should present the
    generated questions and persist answers through
    rdd_state.initialize_project_state.
    """

    packet = create_requirement_packet(prompt, root)
    return {
        "action": "ask_first_run_questions",
        "questions": packet.open_questions,
        "instruction": "Ask these once, save exact answers to profile.md, parse defaults.json, then continue.",
    }


def run_preplan_critique_phase(root: Path, context_summary: str) -> Dict[str, object]:
    """Write preplan critical-only subagent briefs."""

    paths = write_briefs(root, "preplan", None, context_summary)
    return {"phase": "preplan", "brief_paths": [str(path) for path in paths], "main_agent_next": "Run subagents in parallel, collect findings, then decide."}


def run_todo_generation_phase(root: Path) -> Dict[str, object]:
    """Convert accepted findings into TODOs.

    `critic_ledger.findings_to_todo_seeds` performs deduplication and risk
    ordering. This phase preserves dependency and acceptance-criteria hints
    while creating append-only TODO events.
    """

    seeds = findings_to_todo_seeds(accepted_findings(root))
    created = [
        create_todo(
            root,
            seed["title"],
            rationale=seed.get("rationale", ""),
            risk=seed.get("risk", "medium"),
            dependencies=list(seed.get("dependencies", [])),
            acceptance_criteria=list(seed.get("acceptance_criteria", [])),
            source_finding_id=seed.get("source_finding_id"),
        )
        for seed in seeds
    ]
    return {"created_todos": created, "seed_count": len(seeds)}


def run_execution_phase(root: Path) -> Dict[str, object]:
    """Start the next TODO.

    This function does not edit source code. The main Codex agent must perform
    implementation using the selected TODO and internal skills.
    """

    todo = start_next_todo(root)
    return {"active_todo": todo, "main_agent_next": "Use test-driven-development, implement smallest vertical slice, then run validation."}


def run_validation_phase(root: Path, todo_id: str, kinds: Optional[List[str]] = None) -> Dict[str, object]:
    """Prepare validation evidence and critical validation briefs."""

    selected = select_commands(load_commands(root), kinds or ["test", "lint", "build"])
    report = build_report(todo_id, execute=False, selected=selected, results=[])
    report_path = save_report(root, todo_id, report)
    brief_paths = write_briefs(root, "validation", todo_id, f"Validate TODO {todo_id} using report {report_path}")
    return {"validation_report": str(report_path), "brief_paths": [str(path) for path in brief_paths]}


def run_documentation_phase(root: Path, todo_id: str, changed_files: Optional[List[str]] = None) -> Dict[str, object]:
    """Prepare documentation check report."""

    report = build_doc_sync_report(root, todo_id, changed_files or [])
    report_path = save_doc_report(root, report)
    return {"doc_report": str(report_path), "main_agent_next": "Update required docs or record not_needed rationale."}


def run_improvement_phase(root: Path, todo_id: str, context_summary: str) -> Dict[str, object]:
    """Write improvement critical-only subagent briefs."""

    paths = write_briefs(root, "improvement", todo_id, context_summary)
    return {"phase": "improvement", "brief_paths": [str(path) for path in paths], "main_agent_next": "Accept/reject/defer improvement findings and update TODOs."}


def run_once(root: Path, prompt: str) -> Dict[str, object]:
    """Run one safe orchestration step.

    The script performs context intake, first-run detection, critique brief
    creation, TODO creation from already accepted findings, and starts the next
    TODO. It deliberately does **not** run validation, documentation, or
    improvement phases before the main Codex agent has implemented the active
    TODO. Those phases must be called explicitly after implementation evidence
    exists.
    """

    context_result = run_context_phase(root, prompt)
    result: Dict[str, object] = {"context": context_result}
    if needs_first_run(root):
        result["first_run"] = build_first_run_action(root, prompt)
        return result
    result["preplan"] = run_preplan_critique_phase(root, json.dumps(context_result["requirement_packet"], ensure_ascii=False)[:2000])
    result["todo_generation"] = run_todo_generation_phase(root)
    result["execution"] = run_execution_phase(root)
    active = result["execution"].get("active_todo") if isinstance(result["execution"], dict) else None
    if active:
        todo_id = active.get("todo_id") if isinstance(active, dict) else None
        result["post_execution_next"] = {
            "instruction": "Main agent must implement the active TODO with test-driven-development before validation/documentation/improvement phases.",
            "after_implementation_commands": [
                f"python skills/review-driven-development/scripts/quality_gate.py --root . --todo-id {todo_id} --kinds test,lint,build --record-todo-evidence",
                f"python skills/review-driven-development/scripts/workflow_runner.py --root . --phase validation --todo-id {todo_id}",
                f"python skills/review-driven-development/scripts/workflow_runner.py --root . --phase documentation --todo-id {todo_id}",
                f"python skills/review-driven-development/scripts/workflow_runner.py --root . --phase improvement --todo-id {todo_id}",
            ],
        }
    return result


def main() -> None:
    """CLI entrypoint for workflow preview and explicit phase preparation."""

    parser = argparse.ArgumentParser(description="Preview review-driven-development orchestration.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--phase", choices=["once", "context", "first-run", "preplan", "todo-generation", "execution", "validation", "documentation", "improvement"], default="once")
    parser.add_argument("--todo-id")
    parser.add_argument("--changed-file", action="append", default=[])
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.phase == "once":
        result = run_once(root, args.prompt)
    elif args.phase == "context":
        result = run_context_phase(root, args.prompt)
    elif args.phase == "first-run":
        result = build_first_run_action(root, args.prompt)
    elif args.phase == "preplan":
        result = run_preplan_critique_phase(root, args.prompt or "preplan critique")
    elif args.phase == "todo-generation":
        result = run_todo_generation_phase(root)
    elif args.phase == "execution":
        result = run_execution_phase(root)
    elif args.phase == "validation":
        if not args.todo_id:
            raise SystemExit("--todo-id is required for validation phase")
        result = run_validation_phase(root, args.todo_id)
    elif args.phase == "documentation":
        if not args.todo_id:
            raise SystemExit("--todo-id is required for documentation phase")
        result = run_documentation_phase(root, args.todo_id, args.changed_file)
    elif args.phase == "improvement":
        if not args.todo_id:
            raise SystemExit("--todo-id is required for improvement phase")
        result = run_improvement_phase(root, args.todo_id, args.prompt or "Review implementation quality, efficiency, accuracy, documentation, and maintainability after TODO implementation.")
    else:  # pragma: no cover
        raise SystemExit(f"Unknown phase: {args.phase}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
