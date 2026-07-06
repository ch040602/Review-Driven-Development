#!/usr/bin/env python3
"""
TODO ledger helper for the review-driven-development skill.

Role:
- Append TODO lifecycle events to `todos.jsonl`.
- Reconstruct current TODO status from the event ledger.
- Enforce the one-in-progress TODO rule.
- Store validation, review, and documentation evidence.

Implementation notes:
- Events are append-only JSONL records under `.codex/review-driven-development/`.
- Records include the flat state-schema fields (`event`, `created_at`,
  `evidence`, `review_refs`, `doc_refs`) and keep nested
  `validation`/`documentation`/`review` fields for backward compatibility.
- GitHub PR comment import is handled through accepted critic findings before
  TODO creation, not by this ledger directly.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

STATE_DIR = Path(".codex") / "review-driven-development"
TODOS_FILE = "todos.jsonl"
TODO_ARCHIVE_DIR = "todo_archive"
VALID_STATUSES = {"pending", "in_progress", "blocked", "completed", "deferred"}
VALID_RISKS = {"low", "medium", "high", "blocker"}
REQUIRED_TODO_FIELDS = {
    "todo_id", "status", "title", "rationale", "dependencies", "acceptance_criteria",
    "expected_files", "validation", "documentation", "review", "risk",
}


def now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_stamp() -> str:
    """Return a compact UTC timestamp for archive filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def todos_path(root: Path) -> Path:
    """Return TODO ledger path, creating the parent directory."""
    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / TODOS_FILE
    path.touch(exist_ok=True)
    return path


def todo_archive_dir(root: Path) -> Path:
    """Return completed TODO archive directory, creating it if needed."""
    directory = root / STATE_DIR / TODO_ARCHIVE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_events(root: Path) -> List[Dict[str, Any]]:
    """Read append-only TODO events."""
    path = todos_path(root)
    events: List[Dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSONL at {path}:{line_number}: {exc}") from exc
    return events


def deep_merge(left: Dict[str, Any], right: Mapping[str, Any]) -> Dict[str, Any]:
    """Merge nested dictionaries while replacing non-dict values."""
    merged = dict(left)
    for key, value in right.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def current_state(events: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Materialize current TODO state from ledger events."""
    state: Dict[str, Dict[str, Any]] = {}
    for event in events:
        todo_id = event.get("todo_id") or event.get("id")
        if not todo_id:
            raise KeyError("TODO event is missing both 'todo_id' and legacy 'id'")
        normalized = dict(event)
        normalized.setdefault("todo_id", todo_id)
        if "acceptance_criteria" not in normalized and "acceptance" in normalized:
            normalized["acceptance_criteria"] = normalized["acceptance"]
        state[todo_id] = deep_merge(state.get(todo_id, {}), normalized)
    return state


def validate_status(status: str) -> None:
    """Raise if status is invalid."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}. Expected one of {sorted(VALID_STATUSES)}")


def validate_todo_shape(todo: Mapping[str, Any]) -> List[str]:
    """Return missing required TODO fields."""
    return sorted(REQUIRED_TODO_FIELDS - set(todo.keys()))


def assert_single_in_progress(state: Mapping[str, Mapping[str, Any]], *, excluding: Optional[str] = None) -> None:
    """Ensure at most one TODO is in progress."""
    active = [todo_id for todo_id, todo in state.items() if todo.get("status") == "in_progress" and todo_id != excluding]
    if active:
        raise RuntimeError(f"Another TODO is already in_progress: {active}")


def append_event(root: Path, event: Dict[str, Any]) -> Dict[str, Any]:
    """Append a TODO event after validation."""
    event = dict(event)
    event.setdefault("event_id", str(uuid.uuid4()))
    event.setdefault("schema_version", 1)
    event.setdefault("created_at", now_iso())
    event.setdefault("timestamp", event["created_at"])
    if "event" not in event and "event_type" in event:
        event["event"] = event["event_type"]
    if "event_type" not in event and "event" in event:
        event["event_type"] = event["event"]
    validate_status(event.get("status", "pending"))
    state = current_state(read_events(root))
    if event.get("status") == "in_progress":
        assert_single_in_progress(state, excluding=event["todo_id"])
    with todos_path(root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def next_todo_id(state: Mapping[str, Mapping[str, Any]]) -> str:
    """Generate the next TODO ID."""
    return f"RDD-T-{len(state) + 1:08d}"


def base_todo(
    todo_id: str,
    title: str,
    *,
    rationale: str = "",
    risk: str = "medium",
    dependencies: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    expected_files: Optional[List[str]] = None,
    source_finding_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a complete TODO object with default gates."""
    if risk not in VALID_RISKS:
        raise ValueError(f"Invalid risk: {risk}. Expected one of {sorted(VALID_RISKS)}")
    created_at = now_iso()
    return {
        "schema_version": 1,
        "todo_id": todo_id,
        "created_at": created_at,
        "timestamp": created_at,
        "event": "create",
        "event_type": "created",
        "status": "pending",
        "title": title,
        "rationale": rationale,
        "dependencies": dependencies or [],
        "acceptance_criteria": acceptance_criteria or [],
        "expected_files": expected_files or [],
        "evidence": [],
        "review_refs": [],
        "doc_refs": [],
        "validation": {"commands": [], "evidence": []},
        "documentation": {"required": True, "targets": ["implementation-log.md"], "status": "not_started"},
        "review": {"required": True, "subagents": [], "findings": []},
        "risk": risk,
        "source_finding_id": source_finding_id,
    }


def create_todo(
    root: Path,
    title: str,
    *,
    rationale: str = "",
    risk: str = "medium",
    dependencies: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    expected_files: Optional[List[str]] = None,
    source_finding_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a pending TODO."""
    state = current_state(read_events(root))
    todo = base_todo(
        next_todo_id(state),
        title,
        rationale=rationale,
        risk=risk,
        dependencies=dependencies,
        acceptance_criteria=acceptance_criteria,
        expected_files=expected_files,
        source_finding_id=source_finding_id,
    )
    missing = validate_todo_shape(todo)
    if missing:
        raise ValueError(f"TODO is missing required fields: {missing}")
    return append_event(root, todo)


def create_todos_from_findings(root: Path, findings: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Convert accepted critical findings into TODOs.

    Main agent must filter accepted findings before calling this function.
    """
    created: List[Dict[str, Any]] = []
    for finding in findings:
        severity = str(finding.get("severity", "medium"))
        risk = "blocker" if severity == "blocker" else "high" if severity == "high" else "medium" if severity == "medium" else "low"
        title = str(finding.get("recommendation") or finding.get("claim") or "Address accepted critique")
        created.append(create_todo(
            root,
            title,
            rationale=str(finding.get("risk") or finding.get("missing_evidence") or "Accepted critical finding"),
            risk=risk,
            dependencies=[str(item) for item in finding.get("dependencies", [])] if isinstance(finding.get("dependencies", []), list) else [],
            acceptance_criteria=[str(finding.get("check", "Evidence exists for the accepted critique."))],
            source_finding_id=str(finding.get("finding_id") or ""),
        ))
    return created


def get_todo(root: Path, todo_id: str) -> Dict[str, Any]:
    """Return one TODO by ID."""
    state = current_state(read_events(root))
    if todo_id not in state:
        raise KeyError(f"Unknown TODO: {todo_id}")
    return state[todo_id]


def list_todos(root: Path, status: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Return materialized TODOs, optionally filtered by status."""
    state = current_state(read_events(root))
    if status is None:
        return state
    validate_status(status)
    return {todo_id: todo for todo_id, todo in state.items() if todo.get("status") == status}


def set_status(root: Path, todo_id: str, status: str, note: str = "") -> Dict[str, Any]:
    """Set TODO status through an append-only event."""
    get_todo(root, todo_id)
    return append_event(root, {"todo_id": todo_id, "event": "status", "event_type": "status_changed", "status": status, "note": note})


def start_next_todo(root: Path) -> Dict[str, Any] | None:
    """Start the first pending TODO whose dependencies are completed.

    Returns the materialized TODO after the status update so downstream workflow
    phases can still inspect acceptance criteria, expected files, and docs gates.
    """
    state = current_state(read_events(root))
    assert_single_in_progress(state)
    for todo_id, todo in sorted(state.items()):
        if todo.get("status") != "pending":
            continue
        deps = todo.get("dependencies", [])
        if all(state.get(dep, {}).get("status") == "completed" for dep in deps):
            set_status(root, todo_id, "in_progress", "Started by start_next_todo")
            return get_todo(root, todo_id)
    return None


def add_validation_evidence(root: Path, todo_id: str, evidence: str, *, command: str | None = None, metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Append validation evidence to a TODO."""
    current = get_todo(root, todo_id)
    raw_validation = current.get("validation", {})
    if isinstance(raw_validation, Mapping):
        validation = dict(raw_validation)
    elif isinstance(raw_validation, list):
        validation = {"commands": [str(item) for item in raw_validation], "evidence": []}
    else:
        validation = {"commands": [], "evidence": []}
    evidence_list = list(validation.get("evidence", []))
    evidence_list.append(evidence)
    validation["evidence"] = evidence_list
    flat_evidence = list(current.get("evidence", []))
    flat_record: Dict[str, Any] = {"evidence": evidence}
    if command:
        commands = list(validation.get("commands", []))
        commands.append(command)
        validation["commands"] = commands
        flat_record["command"] = command
    if metadata:
        flat_record.update(dict(metadata))
    flat_evidence.append(flat_record)
    return append_event(root, {"todo_id": todo_id, "event": "evidence", "event_type": "validation_evidence_added", "status": current.get("status", "pending"), "evidence": flat_evidence, "validation": validation})


def add_review_findings(root: Path, todo_id: str, findings: Iterable[Mapping[str, Any]], *, subagent: str = "validation-critic") -> Dict[str, Any]:
    """Append critical subagent findings to a TODO."""
    current = get_todo(root, todo_id)
    review = dict(current.get("review", {}))
    review["subagents"] = list(dict.fromkeys([*review.get("subagents", []), subagent]))
    review["findings"] = [*review.get("findings", []), *[dict(item) for item in findings]]
    review_refs = list(current.get("review_refs", []))
    review_refs.append({"subagent": subagent, "finding_count": len(review["findings"]), "recorded_at": now_iso()})
    return append_event(root, {"todo_id": todo_id, "event": "review_ref", "event_type": "review_findings_added", "status": current.get("status", "pending"), "review_refs": review_refs, "review": review})


def add_review_record(root: Path, todo_id: str, *, subagent: str = "validation-runner-critic", summary: str = "Independent critical review completed.", findings: Optional[Iterable[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    """Record an independent validation/review pass for a TODO.

    This is the CLI-friendly wrapper for review evidence. Passing no findings is
    allowed when the reviewer found no blocker/high issue; the review record still
    proves that a separate critic checked the TODO.
    """
    finding_list = [dict(item) for item in (findings or [])]
    current = get_todo(root, todo_id)
    review = dict(current.get("review", {}))
    review["subagents"] = list(dict.fromkeys([*review.get("subagents", []), subagent]))
    review["findings"] = [*review.get("findings", []), *finding_list]
    review_refs = list(current.get("review_refs", []))
    review_refs.append({
        "subagent": subagent,
        "summary": summary,
        "finding_count": len(finding_list),
        "recorded_at": now_iso(),
    })
    return append_event(root, {
        "todo_id": todo_id,
        "event": "review_ref",
        "event_type": "review_record_added",
        "status": current.get("status", "pending"),
        "review_refs": review_refs,
        "review": review,
    })


def update_documentation_status(root: Path, todo_id: str, status: str, targets: Optional[List[str]] = None, note: str = "") -> Dict[str, Any]:
    """Update documentation status for a TODO."""
    current = get_todo(root, todo_id)
    documentation = dict(current.get("documentation", {}))
    documentation["status"] = status
    if targets is not None:
        documentation["targets"] = targets
    if note:
        documentation["note"] = note
    doc_refs = list(current.get("doc_refs", []))
    doc_refs.append({"status": status, "targets": targets if targets is not None else documentation.get("targets", []), "note": note, "recorded_at": now_iso()})
    return append_event(root, {"todo_id": todo_id, "event": "doc_ref", "event_type": "documentation_status_changed", "status": current.get("status", "pending"), "doc_refs": doc_refs, "documentation": documentation})


def completion_blockers(todo: Mapping[str, Any]) -> List[str]:
    """Return reasons a TODO cannot be completed."""
    blockers: List[str] = []
    if not todo.get("acceptance_criteria"):
        blockers.append("missing acceptance criteria")
    if not todo.get("validation", {}).get("evidence"):
        blockers.append("missing validation evidence")
    doc = todo.get("documentation", {})
    if doc.get("required", True) and doc.get("status") not in {"updated", "not_needed"}:
        blockers.append("documentation not updated or justified as not needed")
    review_refs = todo.get("review_refs", [])
    review = todo.get("review", {})
    if review.get("required", True) and not review_refs and not review.get("subagents"):
        blockers.append("missing independent validation/review record")
    findings = todo.get("review", {}).get("findings", [])
    resolved_decisions = {"reject", "rejected", "defer", "deferred", "resolved"}
    unresolved = [f for f in findings if f.get("severity") in {"blocker", "high"} and f.get("decision") not in resolved_decisions]
    if unresolved:
        blockers.append(f"unresolved blocker/high review findings: {len(unresolved)}")
    return blockers


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def configured_quality_commands(root: Path) -> Dict[str, List[str]]:
    """Return configured test/lint/build/eval commands from RDD state."""

    state_dir = root / STATE_DIR
    commands = _load_json(state_dir / "commands.json")
    if not commands:
        commands = _load_json(state_dir / "defaults.json").get("commands", {})
    normalized: Dict[str, List[str]] = {}
    if not isinstance(commands, Mapping):
        return normalized
    for kind in ("test", "lint", "build", "eval"):
        value = commands.get(kind, [])
        if isinstance(value, str):
            normalized[kind] = [value] if value.strip() else []
        elif isinstance(value, list):
            normalized[kind] = [str(item) for item in value if str(item).strip()]
        else:
            normalized[kind] = []
    return normalized


def has_configured_quality_commands(root: Path) -> bool:
    """Return True when any real quality-gate command is configured."""

    return any(configured_quality_commands(root).values())


def has_executed_passing_quality_gate(todo: Mapping[str, Any]) -> bool:
    """Return True when TODO evidence includes an executed passing quality gate."""

    for item in todo.get("evidence", []):
        if not isinstance(item, Mapping):
            continue
        if item.get("source") == "quality_gate" and item.get("execute") is True and item.get("passed") is True:
            return True
    return False


def complete_todo_if_ready(root: Path, todo_id: str, note: str = "") -> Dict[str, Any]:
    """Mark a TODO completed only after all gates are satisfied."""
    todo = get_todo(root, todo_id)
    blockers = completion_blockers(todo)
    if has_configured_quality_commands(root) and not has_executed_passing_quality_gate(todo):
        blockers.append("configured quality-gate commands require executed passing quality_gate evidence")
    if blockers:
        raise RuntimeError(f"TODO {todo_id} is not ready for completion: {blockers}")
    return set_status(root, todo_id, "completed", note or "Acceptance, validation, review, and documentation gates satisfied.")


def archive_completed_todos(root: Path, *, keep_latest: int = 0, dry_run: bool = False) -> Dict[str, Any]:
    """Move completed TODO event history to an archive and keep compact stubs.

    The active ledger stays dependency-safe because every archived TODO keeps a
    small `archive_stub` event with `status: completed`. Full validation/review
    history remains in `todo_archive/` for audit when needed.
    """

    if keep_latest < 0:
        raise ValueError("keep_latest must be >= 0")

    path = todos_path(root)
    events = read_events(root)
    state = current_state(events)
    completed_ids = [
        todo_id
        for todo_id, todo in sorted(
            state.items(),
            key=lambda item: str(item[1].get("created_at") or item[1].get("timestamp") or item[0]),
        )
        if todo.get("status") == "completed" and not todo.get("archived")
    ]
    if keep_latest:
        archive_ids = set(completed_ids[:-keep_latest])
    else:
        archive_ids = set(completed_ids)

    archive_events = [event for event in events if (event.get("todo_id") or event.get("id")) in archive_ids]
    active_events = [event for event in events if (event.get("todo_id") or event.get("id")) not in archive_ids]
    archive_path = root / STATE_DIR / TODO_ARCHIVE_DIR / f"completed-{utc_stamp()}.jsonl"
    manifest_path = archive_path.with_suffix(".manifest.json")

    stubs: List[Dict[str, Any]] = []
    for todo_id in sorted(archive_ids):
        todo = state[todo_id]
        todo_events = [event for event in archive_events if (event.get("todo_id") or event.get("id")) == todo_id]
        completion_events = [event for event in todo_events if event.get("status") == "completed"]
        completion_created_at = ""
        if completion_events:
            completion_created_at = str(completion_events[-1].get("created_at") or completion_events[-1].get("timestamp") or "")
        stub_created_at = now_iso()
        stubs.append({
            "schema_version": 1,
            "event_id": str(uuid.uuid4()),
            "created_at": stub_created_at,
            "timestamp": stub_created_at,
            "event": "archive_stub",
            "event_type": "archive_stub",
            "todo_id": todo_id,
            "status": "completed",
            "title": todo.get("title", ""),
            "risk": todo.get("risk", "medium"),
            "dependencies": todo.get("dependencies", []),
            "acceptance_criteria": todo.get("acceptance_criteria", []),
            "archived": True,
            "archive_path": str(archive_path.relative_to(root)),
            "archived_event_count": len(todo_events),
            "completion_created_at": completion_created_at,
        })

    result = {
        "archived_todo_count": len(archive_ids),
        "archived_event_count": len(archive_events),
        "active_event_count_before": len(events),
        "active_event_count_after": len(active_events) + len(stubs),
        "archive_path": str(archive_path),
        "manifest_path": str(manifest_path),
        "dry_run": dry_run,
    }
    if dry_run or not archive_ids:
        return result

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with archive_path.open("w", encoding="utf-8") as handle:
        for event in archive_events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    manifest = {
        "schema_version": 1,
        "created_at": now_iso(),
        "source_ledger": str(path.relative_to(root)),
        "archive_path": str(archive_path.relative_to(root)),
        "archived_todo_ids": sorted(archive_ids),
        "archived_event_count": len(archive_events),
        "active_event_count_before": len(events),
        "active_event_count_after": len(active_events) + len(stubs),
        "stub_policy": "keep completed archive_stub records in active ledger for dependency checks",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with path.open("w", encoding="utf-8") as handle:
        for event in active_events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        for stub in stubs:
            handle.write(json.dumps(stub, ensure_ascii=False) + "\n")
    return result


def update_from_improvement_critique(root: Path, findings: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Create follow-up TODOs from accepted improvement critique findings."""
    return create_todos_from_findings(root, findings)


def main() -> None:
    """CLI entrypoint for TODO ledger operations."""

    parser = argparse.ArgumentParser(description="Manage review-driven-development TODO ledger.")
    parser.add_argument("--root", default=".", help="Target project root")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("title")
    create_parser.add_argument("--rationale", default="")
    create_parser.add_argument("--risk", default="medium", choices=sorted(VALID_RISKS))
    create_parser.add_argument("--acceptance", action="append", default=[])
    create_parser.add_argument("--expected-file", action="append", default=[])
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", choices=sorted(VALID_STATUSES))
    list_parser.add_argument("--json", action="store_true")
    subparsers.add_parser("start-next")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("todo_id")
    status_parser.add_argument("status", choices=sorted(VALID_STATUSES))
    status_parser.add_argument("--note", default="")
    evidence_parser = subparsers.add_parser("evidence")
    evidence_parser.add_argument("todo_id")
    evidence_parser.add_argument("evidence")
    evidence_parser.add_argument("--command", dest="validation_command")
    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("todo_id")
    review_parser.add_argument("--subagent", default="validation-runner-critic")
    review_parser.add_argument("--summary", default="Independent critical review completed.")
    review_parser.add_argument("--finding-json", action="append", default=[])
    docs_parser = subparsers.add_parser("docs")
    docs_parser.add_argument("todo_id")
    docs_parser.add_argument("status")
    docs_parser.add_argument("--target", action="append")
    docs_parser.add_argument("--note", default="")
    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("todo_id")
    complete_parser.add_argument("--note", default="")
    archive_parser = subparsers.add_parser("archive-completed")
    archive_parser.add_argument("--keep-latest", type=int, default=0, help="Keep the latest N completed TODO histories in todos.jsonl")
    archive_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.command == "create":
        print(json.dumps(create_todo(root, args.title, rationale=args.rationale, risk=args.risk, acceptance_criteria=args.acceptance, expected_files=args.expected_file), ensure_ascii=False, indent=2))
    elif args.command == "list":
        state = list_todos(root, args.status)
        if args.json:
            print(json.dumps(state, ensure_ascii=False, indent=2))
        else:
            for todo_id, todo in sorted(state.items()):
                print(f"{todo_id}\t{todo.get('status')}\t{todo.get('risk')}\t{todo.get('title', '')}")
    elif args.command == "start-next":
        print(json.dumps(start_next_todo(root), ensure_ascii=False, indent=2))
    elif args.command == "status":
        print(json.dumps(set_status(root, args.todo_id, args.status, args.note), ensure_ascii=False, indent=2))
    elif args.command == "evidence":
        print(json.dumps(add_validation_evidence(root, args.todo_id, args.evidence, command=args.validation_command), ensure_ascii=False, indent=2))
    elif args.command == "review":
        findings = [json.loads(item) for item in args.finding_json]
        print(json.dumps(add_review_record(root, args.todo_id, subagent=args.subagent, summary=args.summary, findings=findings), ensure_ascii=False, indent=2))
    elif args.command == "docs":
        print(json.dumps(update_documentation_status(root, args.todo_id, args.status, targets=args.target, note=args.note), ensure_ascii=False, indent=2))
    elif args.command == "complete":
        print(json.dumps(complete_todo_if_ready(root, args.todo_id, args.note), ensure_ascii=False, indent=2))
    elif args.command == "archive-completed":
        print(json.dumps(archive_completed_todos(root, keep_latest=args.keep_latest, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
