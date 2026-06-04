#!/usr/bin/env python3
"""
Project-local state helper for the review-driven-development skill.

Role:
- Create and maintain `.codex/review-driven-development/`.
- Persist exact first-run answers in `profile.md`.
- Persist parsed defaults in `defaults.json` and reuse them by default.
- Append decisions, review summaries, and implementation notes to ledgers.

Implementation notes:
- First-run parsing is conservative and never weakens safety defaults.
- State files remain append-only unless a migration is explicitly recorded.
- GitHub review comments enter the workflow as critic findings when
  `gh-address-comments` is available and approved.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

STATE_DIR = Path(".codex") / "review-driven-development"
PROFILE_FILE = "profile.md"
DEFAULTS_FILE = "defaults.json"
TODOS_FILE = "todos.jsonl"
DECISION_LOG_FILE = "decision-log.md"
REVIEW_LEDGER_FILE = "review-ledger.md"
IMPLEMENTATION_LOG_FILE = "implementation-log.md"
COMMANDS_FILE = "commands.json"
CONTEXT_INVENTORY_FILE = "context-inventory.json"
SCHEMA_VERSION = 1
LEDGER_FILES = [TODOS_FILE, DECISION_LOG_FILE, REVIEW_LEDGER_FILE, IMPLEMENTATION_LOG_FILE]


def now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def filename_timestamp() -> str:
    """Return a filename-safe UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_root(root: str | Path) -> Path:
    """Resolve and validate the target project root."""
    path = Path(root).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Project root does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Project root must be a directory: {path}")
    return path


def state_path(root: str | Path) -> Path:
    """Return the persistent state directory path for a project root."""
    return resolve_root(root) / STATE_DIR


def initial_text_for(filename: str) -> str:
    """Return default content for a new state file."""
    if filename.endswith(".md"):
        title = filename.replace(".md", "").replace("-", " ").title()
        return f"# {title}\n\n"
    return ""


def ensure_state(root: str | Path) -> Path:
    """Create the state directory and baseline ledger files without overwriting."""
    directory = state_path(root)
    directory.mkdir(parents=True, exist_ok=True)
    for filename in LEDGER_FILES:
        path = directory / filename
        if not path.exists():
            path.write_text(initial_text_for(filename), encoding="utf-8")
    return directory


def read_json(path: Path, default: Any = None) -> Any:
    """Read a JSON file; return `default` if absent."""
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Mapping[str, Any], *, force: bool = False) -> Path:
    """Write deterministic UTF-8 JSON with explicit overwrite control."""
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path}. Use force=True to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def default_defaults() -> Dict[str, Any]:
    """Return conservative first-run defaults for the skill."""
    timestamp = now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": timestamp,
        "updated_at": timestamp,
        "language": {"user_facing": "ko", "documentation": "ko", "preserve_code_terms": True},
        "priority": {"completeness_over_speed": True, "safety_over_scope": True, "minimize_destructive_changes": True},
        "existing_code_policy": "review_then_reuse",
        "implementation_method": "tdd_first_incremental",
        "source_grounding": True,
        "markdown_context": True,
        "parallel_subagent_policy": "maximize_where_safe",
        "critical_subagents": {"preplan": True, "validation": True, "improvement": True, "contract": "critical_only_no_final_decision"},
        "documentation": {"always_document_completed_todos": True, "default_targets": ["README.md", "docs/", "implementation-log.md"], "adr_for_significant_design_decisions": True},
        "data_analysis": {"data_critic_on_csv_or_logs": True, "preserve_raw_data": True, "require_schema_notes": True},
        "review_comments_to_todos": True,
        "ask_before_destructive_changes": True,
        "commands": {"test": [], "lint": [], "build": [], "eval": []},
    }


def normalize_language(value: str | None, fallback: str = "ko") -> str:
    """Normalize language labels to `ko` or `en`."""
    if not value:
        return fallback
    lowered = value.strip().lower()
    if lowered in {"ko", "kr", "korean", "한국어", "한글"}:
        return "ko"
    if lowered in {"en", "eng", "english", "영어"}:
        return "en"
    return fallback


def merge_preserving_safety(base: MutableMapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    """Merge defaults while preserving destructive-change safety settings."""
    merged: Dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    if base.get("ask_before_destructive_changes", True):
        merged["ask_before_destructive_changes"] = True
    priority = dict(merged.get("priority", {}))
    if base.get("priority", {}).get("minimize_destructive_changes", True):
        priority["minimize_destructive_changes"] = True
    merged["priority"] = priority
    return merged


def parse_command_hints(exact_answers: str) -> Dict[str, list[str]]:
    """Extract common test/lint/build/eval commands from free text.

    Codex should replace this with structured questionnaire parsing.
    """
    hints = {
        "test": ["npm test", "pnpm test", "yarn test", "pytest", "go test", "cargo test"],
        "lint": ["npm run lint", "pnpm lint", "yarn lint", "ruff check", "eslint", "cargo clippy"],
        "build": ["npm run build", "pnpm build", "yarn build", "cargo build", "go build"],
        "eval": ["npm run eval", "pnpm eval", "pytest eval", "python eval.py"],
    }
    found: Dict[str, list[str]] = {kind: [] for kind in hints}
    for kind, commands in hints.items():
        for command in commands:
            if command in exact_answers:
                found[kind].append(command)
    return found


def parse_first_run_answers(exact_answers: str, inventory: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Parse first-run answers into durable defaults.

    Current implementation is heuristic and conservative. It records inventory
    hints but does not silently weaken review, validation, or safety settings.
    """
    defaults = default_defaults()
    text = exact_answers.lower()
    if "english" in text or "영어" in text or " en" in f" {text}":
        defaults["language"]["user_facing"] = "en"
    if "korean" in text or "한국어" in text or "한글" in text or " ko" in f" {text}":
        defaults["language"]["user_facing"] = "ko"
    if "rewrite" in text or "재작성" in text:
        defaults["existing_code_policy"] = "ask_then_rewrite"
    elif "refactor" in text or "리팩터" in text or "리팩토" in text:
        defaults["existing_code_policy"] = "review_then_refactor"
    elif "reuse" in text or "재사용" in text:
        defaults["existing_code_policy"] = "review_then_reuse"
    for kind, values in parse_command_hints(exact_answers).items():
        defaults["commands"][kind].extend(values)
    if inventory:
        defaults["context_inventory_hint"] = {
            "primary_languages": list(inventory.get("primary_languages", [])),
            "has_existing_code": bool(inventory.get("has_existing_code")),
            "has_tests": bool(inventory.get("has_tests")),
            "requires_data_critic": bool(inventory.get("requires_data_critic")),
        }
    defaults["updated_at"] = now_iso()
    return defaults


def load_defaults(root: str | Path) -> Dict[str, Any] | None:
    """Load project defaults if initialized."""
    return read_json(state_path(root) / DEFAULTS_FILE, default=None)


def write_defaults(root: str | Path, defaults: Mapping[str, Any], *, force: bool = False) -> Path:
    """Persist parsed defaults."""
    directory = ensure_state(root)
    normalized: Dict[str, Any] = dict(defaults)
    normalized.setdefault("schema_version", SCHEMA_VERSION)
    normalized.setdefault("created_at", now_iso())
    normalized["updated_at"] = now_iso()
    return write_json(directory / DEFAULTS_FILE, normalized, force=force)


def write_profile(root: str | Path, exact_answers: str, *, force: bool = False) -> Path:
    """Persist the exact first-run answer as Markdown."""
    directory = ensure_state(root)
    path = directory / PROFILE_FILE
    if path.exists() and not force:
        raise FileExistsError(f"Profile already exists: {path}. Use force=True to overwrite.")
    text = (
        "# review-driven-development first-run profile\n\n"
        f"- Created at: {now_iso()}\n"
        "- Purpose: Preserve the first-run answer permanently and use parsed defaults when no override is provided.\n\n"
        "## Exact user answers\n\n"
        "```text\n"
        f"{exact_answers.strip()}\n"
        "```\n\n"
        "## Parsed defaults\n\n"
        f"See `{DEFAULTS_FILE}`.\n"
    )
    path.write_text(text, encoding="utf-8")
    return path


def initialize_project_state(root: str | Path, exact_answers: str, *, inventory: Optional[Mapping[str, Any]] = None, parsed_defaults: Optional[Mapping[str, Any]] = None, force: bool = False) -> Dict[str, str]:
    """Initialize profile and defaults together after the first-run questionnaire."""
    defaults = dict(parsed_defaults or parse_first_run_answers(exact_answers, inventory))
    return {
        "profile": str(write_profile(root, exact_answers, force=force)),
        "defaults": str(write_defaults(root, defaults, force=force)),
    }


def update_defaults(root: str | Path, override: Mapping[str, Any], *, force: bool = True) -> Path:
    """Update defaults using conservative merge semantics."""
    current = load_defaults(root) or default_defaults()
    return write_defaults(root, merge_preserving_safety(current, override), force=force)


def append_markdown(root: str | Path, filename: str, heading: str, body: str) -> Path:
    """Append a timestamped Markdown section to a state ledger."""
    directory = ensure_state(root)
    path = directory / filename
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {heading}\n\n")
        handle.write(f"- Timestamp: {now_iso()}\n\n")
        handle.write(body.rstrip() + "\n")
    return path


def append_decision(root: str | Path, decision_id: str, body: str) -> Path:
    """Append an accepted/rejected/deferred critique decision."""
    return append_markdown(root, DECISION_LOG_FILE, f"Decision {decision_id}", body)


def append_review_summary(root: str | Path, phase: str, body: str) -> Path:
    """Append a critical subagent review summary."""
    return append_markdown(root, REVIEW_LEDGER_FILE, f"Review summary: {phase}", body)


def append_implementation_log(root: str | Path, todo_id: str, body: str) -> Path:
    """Append implementation evidence for a completed or blocked TODO."""
    return append_markdown(root, IMPLEMENTATION_LOG_FILE, f"TODO {todo_id}", body)


def update_commands(root: str | Path, commands: Mapping[str, Iterable[str]], *, force: bool = True) -> Path:
    """Write project-specific quality-gate commands."""
    directory = ensure_state(root)
    normalized = {kind: list(values) for kind, values in commands.items()}
    return write_json(directory / COMMANDS_FILE, normalized, force=force)


def load_context_inventory(root: str | Path) -> Dict[str, Any] | None:
    """Load saved context inventory if present."""
    return read_json(state_path(root) / CONTEXT_INVENTORY_FILE, default=None)


def status(root: str | Path) -> Dict[str, Any]:
    """Return a compact state summary."""
    directory = state_path(root)
    defaults = load_defaults(root)
    files = {name: (directory / name).exists() for name in [PROFILE_FILE, DEFAULTS_FILE, *LEDGER_FILES, COMMANDS_FILE, CONTEXT_INVENTORY_FILE]}
    return {
        "schema_version": SCHEMA_VERSION,
        "state_dir": str(directory),
        "exists": directory.exists(),
        "files": files,
        "has_defaults": defaults is not None,
        "language": (defaults or {}).get("language"),
        "existing_code_policy": (defaults or {}).get("existing_code_policy"),
        "implementation_method": (defaults or {}).get("implementation_method"),
    }


def main() -> None:
    """Command-line entrypoint for state operations."""
    parser = argparse.ArgumentParser(description="Manage review-driven-development project state.")
    parser.add_argument("--root", default=".", help="Target project root")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ensure", help="Create state directory and ledger files")
    init_parser = subparsers.add_parser("init-defaults", help="Write profile.md and defaults.json")
    init_parser.add_argument("--answers", required=True)
    init_parser.add_argument("--defaults-json")
    init_parser.add_argument("--inventory-json")
    init_parser.add_argument("--force", action="store_true")
    commands_parser = subparsers.add_parser("set-commands", help="Write commands.json")
    commands_parser.add_argument("--commands-json", required=True)
    append_parser = subparsers.add_parser("append", help="Append to a Markdown ledger")
    append_parser.add_argument("filename", choices=[DECISION_LOG_FILE, REVIEW_LEDGER_FILE, IMPLEMENTATION_LOG_FILE])
    append_parser.add_argument("heading")
    append_parser.add_argument("body")
    subparsers.add_parser("status", help="Print state status")
    args = parser.parse_args()
    root = resolve_root(args.root)
    if args.command == "ensure":
        print(ensure_state(root))
    elif args.command == "init-defaults":
        inventory = json.loads(args.inventory_json) if args.inventory_json else None
        parsed = json.loads(args.defaults_json) if args.defaults_json else None
        print(json.dumps(initialize_project_state(root, args.answers, inventory=inventory, parsed_defaults=parsed, force=args.force), ensure_ascii=False, indent=2))
    elif args.command == "set-commands":
        print(update_commands(root, json.loads(args.commands_json)))
    elif args.command == "append":
        print(append_markdown(root, args.filename, args.heading, args.body))
    elif args.command == "status":
        print(json.dumps(status(root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
