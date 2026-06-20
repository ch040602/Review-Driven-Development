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
    from .context_inventory import load_context_pack, load_semantic_index, search_semantic_index, summarize_inventory, summarize_semantic_index, sync_context, write_bootstrap
    from .critic_ledger import accepted_findings, findings_to_todo_seeds
    from .doc_sync_check import build_doc_sync_report, save_report as save_doc_report
    from .quality_gate import build_report, load_commands, save_report, select_commands
    from .rdd_state import ensure_state, load_defaults
    from .requirement_analyzer import create_requirement_packet, packet_to_dict
    from .subagent_brief_builder import allocation_table_for_roles, write_briefs
    from .todo_manager import create_todo, start_next_todo
except ImportError:  # pragma: no cover
    from context_inventory import load_context_pack, load_semantic_index, search_semantic_index, summarize_inventory, summarize_semantic_index, sync_context, write_bootstrap  # type: ignore
    from critic_ledger import accepted_findings, findings_to_todo_seeds  # type: ignore
    from doc_sync_check import build_doc_sync_report, save_report as save_doc_report  # type: ignore
    from quality_gate import build_report, load_commands, save_report, select_commands  # type: ignore
    from rdd_state import ensure_state, load_defaults  # type: ignore
    from requirement_analyzer import create_requirement_packet, packet_to_dict  # type: ignore
    from subagent_brief_builder import allocation_table_for_roles, write_briefs  # type: ignore
    from todo_manager import create_todo, start_next_todo  # type: ignore


def run_context_phase(
    root: Path,
    prompt: str,
    *,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Inventory project context and build a requirement packet."""

    ensure_state(root)
    sync = sync_context(
        root,
        mode=inventory_mode,
        include_snippets=include_snippets,
        enable_embeddings=enable_embeddings,
        embedding_model=embedding_model,
    )
    context = sync["context_inventory"]
    packet = create_requirement_packet(prompt, root, saved_inventory=True)
    return {
        "cache_hit": sync["cache_hit"],
        "context_inventory": context,
        "inventory_path": sync["inventory_path"],
        "context_pack_path": sync["context_pack_path"],
        "cache_path": sync["cache_path"],
        "requirement_packet": packet_to_dict(packet),
    }


def run_sync_phase(
    root: Path,
    *,
    force: bool = False,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Synchronize inventory/cache/context-pack state for fast reuse."""

    ensure_state(root)
    sync = sync_context(
        root,
        force=force,
        mode=inventory_mode,
        include_snippets=include_snippets,
        enable_embeddings=enable_embeddings,
        embedding_model=embedding_model,
    )
    inventory = sync["context_inventory"]
    return {
        "phase": "sync",
        "cache_hit": sync["cache_hit"],
        "inventory_path": sync["inventory_path"],
        "context_pack_path": sync["context_pack_path"],
        "cache_path": sync["cache_path"],
        "summary": summarize_inventory(inventory),
        "main_agent_next": "Open context-pack.md first; open full source files only when the pack points to them.",
    }


def run_overview_phase(
    root: Path,
    *,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Return the compact context pack for quick Codex reference."""

    ensure_state(root)
    sync = sync_context(root, mode=inventory_mode, include_snippets=include_snippets, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
    pack = load_context_pack(root) or summarize_inventory(sync["context_inventory"])
    return {
        "phase": "overview",
        "cache_hit": sync["cache_hit"],
        "context_pack_path": sync["context_pack_path"],
        "context_pack": pack,
    }


def run_semantic_index_phase(
    root: Path,
    *,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Return the bounded semantic locator index for quick file lookup."""

    ensure_state(root)
    sync = sync_context(root, mode=inventory_mode, include_snippets=include_snippets, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
    index = load_semantic_index(root) or {}
    return {
        "phase": "semantic-index",
        "cache_hit": sync["cache_hit"],
        "semantic_index_path": sync.get("semantic_index_path"),
        "semantic_index_summary": summarize_semantic_index(index),
        "symbol_sample": list(index.get("symbols", []))[:20] if isinstance(index, Mapping) else [],
    }


def run_semantic_search_phase(
    root: Path,
    query: str,
    *,
    top_k: int = 8,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    force_tfidf: bool = False,
    force_lexical: bool = False,
) -> Dict[str, object]:
    """Return ranked likely files for a semantic query."""

    ensure_state(root)
    sync = sync_context(root, mode=inventory_mode, include_snippets=include_snippets, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
    return {
        "phase": "semantic-search",
        "cache_hit": sync["cache_hit"],
        "semantic_index_path": sync.get("semantic_index_path"),
        "search": search_semantic_index(query, load_semantic_index(root) or {}, top_k=top_k, force_tfidf=force_tfidf, force_lexical=force_lexical, embedding_model=embedding_model),
    }


def run_role_map_phase(
    root: Path,
    *,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Return compact file responsibility map for targeted exploration."""

    ensure_state(root)
    sync = sync_context(root, mode=inventory_mode, include_snippets=include_snippets, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
    role_map = sync["context_inventory"].get("role_map", [])
    return {
        "phase": "role-map",
        "cache_hit": sync["cache_hit"],
        "context_pack_path": sync["context_pack_path"],
        "role_map": role_map,
        "main_agent_next": "Pick one role path or query hint before opening any broader source tree.",
    }


def run_bootstrap_phase(
    root: Path,
    *,
    target: str = "AGENTS.md",
    force: bool = False,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Write repo-local fast-context bootstrap guidance."""

    ensure_state(root)
    bootstrap_path = write_bootstrap(root, target=target)
    sync = sync_context(root, force=True, mode=inventory_mode, include_snippets=include_snippets, enable_embeddings=enable_embeddings, embedding_model=embedding_model)
    return {
        "phase": "bootstrap",
        "cache_hit": sync["cache_hit"],
        "context_pack_path": sync["context_pack_path"],
        "semantic_index_path": sync.get("semantic_index_path"),
        "bootstrap_path": str(bootstrap_path),
        "main_agent_next": "Codex should read the bootstrap block from AGENTS.md, then context-pack.md, then use the semantic index for targeted file lookup.",
    }


def run_commands_phase(root: Path, todo_id: Optional[str] = None) -> Dict[str, object]:
    """Return common RDD commands for context/cache/TODO/quality UX."""

    ensure_state(root)
    commands = load_commands(root)
    quality_command = None
    if todo_id:
        quality_command = (
            "python skills/review-driven-development/scripts/quality_gate.py "
            f"--root . --todo-id {todo_id} --kinds test,lint,build --execute --record-todo-evidence"
        )
    return {
        "phase": "commands",
        "context": [
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --overview",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search \"<query>\"",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --role-map",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search \"<query>\" --force-tfidf",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search \"<query>\" --force-lexical",
            "python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase overview",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-index",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-search --query \"<query>\"",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase role-map",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase bootstrap",
        ],
        "workflow": [
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase sync",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase once --prompt \"<requirement>\"",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase validation --todo-id <id> --agent-budget spark-first",
            "python skills/review-driven-development/scripts/workflow_runner.py --root . --phase commands",
        ],
        "quality": {
            "configured": commands,
            "execute_current_todo": quality_command,
        },
    }


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


def run_preplan_critique_phase(
    root: Path,
    context_summary: str,
    *,
    critic_depth: str = "standard",
    max_roles: int | None = None,
    context_max_chars: int = 1200,
    agent_budget: str = "spark-first",
) -> Dict[str, object]:
    """Write preplan critical-only subagent briefs."""

    paths = write_briefs(
        root,
        "preplan",
        None,
        context_summary,
        critic_depth=critic_depth,
        max_roles=max_roles,
        context_max_chars=context_max_chars,
        agent_budget=agent_budget,
    )
    roles = [Path(path).stem for path in paths]
    return {
        "phase": "preplan",
        "brief_paths": [str(path) for path in paths],
        "critic_depth": critic_depth,
        "agent_budget": agent_budget,
        "agent_allocations": allocation_table_for_roles(roles, "preplan", critic_depth=critic_depth, agent_budget=agent_budget),
        "main_agent_next": "Run only the generated critical briefs, collect findings, then decide.",
    }


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


def run_validation_phase(
    root: Path,
    todo_id: str,
    kinds: Optional[List[str]] = None,
    *,
    critic_depth: str = "standard",
    max_roles: int | None = None,
    context_max_chars: int = 1200,
    agent_budget: str = "spark-first",
) -> Dict[str, object]:
    """Prepare validation evidence and critical validation briefs."""

    selected = select_commands(load_commands(root), kinds or ["test", "lint", "build"])
    report = build_report(todo_id, execute=False, selected=selected, results=[])
    report_path = save_report(root, todo_id, report)
    brief_paths = write_briefs(
        root,
        "validation",
        todo_id,
        f"Validate TODO {todo_id} using report {report_path}",
        critic_depth=critic_depth,
        max_roles=max_roles,
        context_max_chars=context_max_chars,
        agent_budget=agent_budget,
    )
    roles = [Path(path).stem for path in brief_paths]
    return {
        "validation_report": str(report_path),
        "brief_paths": [str(path) for path in brief_paths],
        "agent_budget": agent_budget,
        "agent_allocations": allocation_table_for_roles(roles, "validation", critic_depth=critic_depth, agent_budget=agent_budget),
    }


def run_documentation_phase(root: Path, todo_id: str, changed_files: Optional[List[str]] = None) -> Dict[str, object]:
    """Prepare documentation check report."""

    report = build_doc_sync_report(root, todo_id, changed_files or [])
    report_path = save_doc_report(root, report)
    return {"doc_report": str(report_path), "main_agent_next": "Update required docs or record not_needed rationale."}


def run_improvement_phase(
    root: Path,
    todo_id: str,
    context_summary: str,
    *,
    critic_depth: str = "standard",
    max_roles: int | None = None,
    context_max_chars: int = 1200,
    agent_budget: str = "spark-first",
) -> Dict[str, object]:
    """Write improvement critical-only subagent briefs."""

    paths = write_briefs(
        root,
        "improvement",
        todo_id,
        context_summary,
        critic_depth=critic_depth,
        max_roles=max_roles,
        context_max_chars=context_max_chars,
        agent_budget=agent_budget,
    )
    roles = [Path(path).stem for path in paths]
    return {
        "phase": "improvement",
        "brief_paths": [str(path) for path in paths],
        "critic_depth": critic_depth,
        "agent_budget": agent_budget,
        "agent_allocations": allocation_table_for_roles(roles, "improvement", critic_depth=critic_depth, agent_budget=agent_budget),
        "main_agent_next": "Accept/reject/defer improvement findings and update TODOs.",
    }


def run_once(
    root: Path,
    prompt: str,
    *,
    inventory_mode: str = "standard",
    include_snippets: bool = False,
    critic_depth: str = "standard",
    max_roles: int | None = None,
    context_max_chars: int = 1200,
    agent_budget: str = "spark-first",
    enable_embeddings: bool = False,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, object]:
    """Run one safe orchestration step.

    The script performs context intake, first-run detection, critique brief
    creation, TODO creation from already accepted findings, and starts the next
    TODO. It deliberately does **not** run validation, documentation, or
    improvement phases before the main Codex agent has implemented the active
    TODO. Those phases must be called explicitly after implementation evidence
    exists.
    """

    context_result = run_context_phase(
        root,
        prompt,
        inventory_mode=inventory_mode,
        include_snippets=include_snippets,
        enable_embeddings=enable_embeddings,
        embedding_model=embedding_model,
    )
    result: Dict[str, object] = {"context": context_result}
    if needs_first_run(root):
        result["first_run"] = build_first_run_action(root, prompt)
        return result
    result["preplan"] = run_preplan_critique_phase(
        root,
        json.dumps(context_result["requirement_packet"], ensure_ascii=False)[:context_max_chars],
        critic_depth=critic_depth,
        max_roles=max_roles,
        context_max_chars=context_max_chars,
        agent_budget=agent_budget,
    )
    result["todo_generation"] = run_todo_generation_phase(root)
    result["execution"] = run_execution_phase(root)
    active = result["execution"].get("active_todo") if isinstance(result["execution"], dict) else None
    if active:
        todo_id = active.get("todo_id") if isinstance(active, dict) else None
        result["post_execution_next"] = {
            "instruction": "Main agent must implement the active TODO with test-driven-development before validation/documentation/improvement phases.",
            "after_implementation_commands": [
                f"python skills/review-driven-development/scripts/quality_gate.py --root . --todo-id {todo_id} --kinds test,lint,build --record-todo-evidence",
                f"python skills/review-driven-development/scripts/workflow_runner.py --root . --phase validation --todo-id {todo_id} --critic-depth {critic_depth} --agent-budget {agent_budget}",
                f"python skills/review-driven-development/scripts/workflow_runner.py --root . --phase documentation --todo-id {todo_id}",
                f"python skills/review-driven-development/scripts/workflow_runner.py --root . --phase improvement --todo-id {todo_id} --critic-depth {critic_depth} --agent-budget {agent_budget}",
            ],
        }
    return result


def main() -> None:
    """CLI entrypoint for workflow preview and explicit phase preparation."""

    parser = argparse.ArgumentParser(description="Preview review-driven-development orchestration.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--phase", choices=["once", "context", "sync", "overview", "semantic-index", "semantic-search", "role-map", "bootstrap", "commands", "first-run", "preplan", "todo-generation", "execution", "validation", "documentation", "improvement"], default="once")
    parser.add_argument("--todo-id")
    parser.add_argument("--query", default="")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--force", action="store_true", help="Force context cache rebuild for sync phase")
    parser.add_argument("--inventory-mode", choices=["fast", "standard", "deep"], default="standard")
    parser.add_argument("--include-snippets", action="store_true")
    parser.add_argument("--critic-depth", choices=["minimal", "standard", "deep"], default="standard")
    parser.add_argument("--max-roles", type=int)
    parser.add_argument("--context-max-chars", type=int, default=1200)
    parser.add_argument("--agent-budget", choices=["spark-first", "balanced", "deep"], default="spark-first")
    parser.add_argument("--embeddings", action="store_true")
    parser.add_argument("--no-embeddings", action="store_true")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--force-tfidf", action="store_true")
    parser.add_argument("--force-lexical", action="store_true")
    parser.add_argument("--bootstrap-target", default="AGENTS.md")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    enable_embeddings = args.embeddings and not args.no_embeddings
    if args.phase == "once":
        result = run_once(
            root,
            args.prompt,
            inventory_mode=args.inventory_mode,
            include_snippets=args.include_snippets,
            critic_depth=args.critic_depth,
            max_roles=args.max_roles,
            context_max_chars=args.context_max_chars,
            agent_budget=args.agent_budget,
            enable_embeddings=enable_embeddings,
            embedding_model=args.embedding_model,
        )
    elif args.phase == "context":
        result = run_context_phase(root, args.prompt, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model)
    elif args.phase == "sync":
        result = run_sync_phase(root, force=args.force, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model)
    elif args.phase == "overview":
        result = run_overview_phase(root, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model)
    elif args.phase == "semantic-index":
        result = run_semantic_index_phase(root, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model)
    elif args.phase == "semantic-search":
        if not args.query:
            raise SystemExit("--query is required for semantic-search phase")
        result = run_semantic_search_phase(root, args.query, top_k=args.top_k, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model, force_tfidf=args.force_tfidf, force_lexical=args.force_lexical)
    elif args.phase == "role-map":
        result = run_role_map_phase(root, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model)
    elif args.phase == "bootstrap":
        result = run_bootstrap_phase(root, target=args.bootstrap_target, force=args.force, inventory_mode=args.inventory_mode, include_snippets=args.include_snippets, enable_embeddings=enable_embeddings, embedding_model=args.embedding_model)
    elif args.phase == "commands":
        result = run_commands_phase(root, args.todo_id)
    elif args.phase == "first-run":
        result = build_first_run_action(root, args.prompt)
    elif args.phase == "preplan":
        result = run_preplan_critique_phase(root, args.prompt or "preplan critique", critic_depth=args.critic_depth, max_roles=args.max_roles, context_max_chars=args.context_max_chars, agent_budget=args.agent_budget)
    elif args.phase == "todo-generation":
        result = run_todo_generation_phase(root)
    elif args.phase == "execution":
        result = run_execution_phase(root)
    elif args.phase == "validation":
        if not args.todo_id:
            raise SystemExit("--todo-id is required for validation phase")
        result = run_validation_phase(root, args.todo_id, critic_depth=args.critic_depth, max_roles=args.max_roles, context_max_chars=args.context_max_chars, agent_budget=args.agent_budget)
    elif args.phase == "documentation":
        if not args.todo_id:
            raise SystemExit("--todo-id is required for documentation phase")
        result = run_documentation_phase(root, args.todo_id, args.changed_file)
    elif args.phase == "improvement":
        if not args.todo_id:
            raise SystemExit("--todo-id is required for improvement phase")
        result = run_improvement_phase(root, args.todo_id, args.prompt or "Review implementation quality, efficiency, accuracy, documentation, and maintainability after TODO implementation.", critic_depth=args.critic_depth, max_roles=args.max_roles, context_max_chars=args.context_max_chars, agent_budget=args.agent_budget)
    else:  # pragma: no cover
        raise SystemExit(f"Unknown phase: {args.phase}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
