#!/usr/bin/env python3
"""
Documentation synchronization checker helper.

Role:
- Identify documentation targets that may need updates after each TODO.
- Produce a report that a documentation critic can challenge.
- Avoid claiming documentation correctness; this only records presence and likely obligations.

Implementation notes:
- TODO metadata and changed files are mapped to likely documentation targets.
- Public-interface diffs, stale example detection, and ADR decisions remain
  critic/main-agent responsibilities backed by this report.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

STATE_DIR = Path(".codex") / "review-driven-development"
DOC_TARGETS = ["README.md", "README.ko.md", "README.en.md", "docs", "CHANGELOG.md", "docs/adr"]
PUBLIC_INTERFACE_HINTS = ("api", "route", "controller", "schema", "types", "interface", "public")
USER_FACING_HINTS = ("ui", "page", "component", "view", "screen", "cli", "command")


def now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def filename_timestamp() -> str:
    """Return timestamp for report filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def path_exists(root: Path, target: str) -> bool:
    """Check whether a documentation target exists."""
    return (root / target).exists()


def discover_docs(root: Path, targets: Iterable[str] = DOC_TARGETS) -> Dict[str, List[str]]:
    """Return found and missing documentation targets."""
    found: List[str] = []
    missing: List[str] = []
    for target in targets:
        if path_exists(root, target):
            found.append(target)
        else:
            missing.append(target)
    return {"found": found, "missing": missing}


def infer_targets_from_files(changed_files: Iterable[str]) -> List[str]:
    """Infer documentation targets from changed files."""
    targets = {".codex/review-driven-development/implementation-log.md"}
    lowered = [path.lower() for path in changed_files]
    if any(any(hint in path for hint in PUBLIC_INTERFACE_HINTS) for path in lowered):
        targets.update({"README.md", "docs/", "docs/adr/"})
    if any(any(hint in path for hint in USER_FACING_HINTS) for path in lowered):
        targets.update({"README.md", "docs/"})
    return sorted(targets)


def load_todo(root: Path, todo_id: str) -> Dict[str, Any] | None:
    """Load a materialized TODO from todos.jsonl if available."""
    path = root / STATE_DIR / "todos.jsonl"
    if not path.exists():
        return None
    state: Dict[str, Dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        todo = dict(state.get(event["todo_id"], {}))
        todo.update(event)
        state[event["todo_id"]] = todo
    return state.get(todo_id)


def infer_targets_for_todo(root: Path, todo_id: Optional[str], changed_files: Iterable[str]) -> List[str]:
    """Infer documentation targets from TODO metadata and changed files."""
    targets = set(infer_targets_from_files(changed_files))
    if todo_id:
        todo = load_todo(root, todo_id)
        if todo:
            for target in todo.get("documentation", {}).get("targets", []):
                targets.add(target)
    return sorted(targets)


def build_doc_sync_report(root: Path, todo_id: Optional[str], changed_files: Iterable[str]) -> Dict[str, Any]:
    """Build a documentation synchronization report."""
    changed = list(changed_files)
    discovered = discover_docs(root)
    inferred = infer_targets_for_todo(root, todo_id, changed)
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "todo_id": todo_id,
        "changed_files": changed,
        "docs_found": discovered["found"],
        "docs_missing": discovered["missing"],
        "inferred_update_targets": inferred,
        "critic_note": "Documentation critic must decide which targets are required and whether content is actually synchronized.",
    }


def save_report(root: Path, report: Mapping[str, Any]) -> Path:
    """Save a documentation sync report under project state."""
    directory = root / STATE_DIR / "doc-reports"
    directory.mkdir(parents=True, exist_ok=True)
    todo_part = str(report.get("todo_id") or "NO-TODO").replace("/", "_")
    path = directory / f"doc-sync-{todo_part}-{filename_timestamp()}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    """CLI entrypoint for documentation synchronization checks."""

    parser = argparse.ArgumentParser(description="Check documentation target presence and inferred update obligations.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--todo-id")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = build_doc_sync_report(root, args.todo_id, args.changed_file)
    if args.save:
        report = dict(report)
        report["saved_to"] = str(save_report(root, report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
