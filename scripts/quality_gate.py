#!/usr/bin/env python3
"""
Quality gate evidence helper for review-driven-development.

Role:
- Load configured test/lint/build/eval commands.
- Print commands by default.
- Execute commands only with `--execute`.
- Save validation evidence for the current TODO.

Use with the `test-driven-development` skill. This records evidence; it does not design tests.

Implementation notes:
- Command discovery is explicit through `commands.json` or `defaults.json`.
- Reports are always saved under the project-local RDD state directory.
- `--record-todo-evidence` links the saved report back to `todos.jsonl`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

STATE_DIR = Path(".codex") / "review-driven-development"
DEFAULT_COMMANDS = {"test": [], "lint": [], "build": [], "eval": []}


def now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def filename_timestamp() -> str:
    """Return timestamp for report filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path, default: Any) -> Any:
    """Load JSON if available, otherwise return default."""
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_commands(commands: Mapping[str, Any]) -> Dict[str, List[str]]:
    """Normalize command mapping into lists for test/lint/build/eval."""
    normalized = dict(DEFAULT_COMMANDS)
    for kind in normalized:
        value = commands.get(kind, [])
        normalized[kind] = [value] if isinstance(value, str) else [str(item) for item in value]
    return normalized


def load_commands(root: Path) -> Dict[str, List[str]]:
    """Load quality-gate commands from commands.json or defaults.json."""
    defaults_path = root / STATE_DIR / "defaults.json"
    commands_path = root / STATE_DIR / "commands.json"
    if commands_path.exists():
        return normalize_commands(load_json(commands_path, DEFAULT_COMMANDS))
    if defaults_path.exists():
        return normalize_commands(load_json(defaults_path, {}).get("commands", DEFAULT_COMMANDS))
    return dict(DEFAULT_COMMANDS)


def select_commands(commands_by_kind: Mapping[str, List[str]], kinds: Iterable[str]) -> List[Tuple[str, str]]:
    """Select commands in stable kind order."""
    return [(kind, command) for kind in kinds for command in commands_by_kind.get(kind, [])]


def run_command(command: str, root: Path, timeout: int) -> Dict[str, Any]:
    """Execute a shell command and return bounded evidence."""
    started = now_iso()
    try:
        result = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True, timeout=timeout)
        return {
            "command": command,
            "started_at": started,
            "finished_at": now_iso(),
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-4000:],
            "stderr_tail": result.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "command": command,
            "started_at": started,
            "finished_at": now_iso(),
            "returncode": None,
            "stdout_tail": stdout[-4000:],
            "stderr_tail": stderr[-4000:],
            "timed_out": True,
            "timeout_seconds": timeout,
        }


def evaluate_results(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Summarize pass/fail status for executed quality gates."""
    if not results:
        return {"passed": False, "reason": "no commands selected or executed"}
    failed = [item for item in results if item.get("returncode") != 0 or item.get("timed_out")]
    return {"passed": not failed, "failed_count": len(failed), "failed_commands": [item.get("command") for item in failed]}


def build_report(todo_id: str, selected: Sequence[Tuple[str, str]], *, execute: bool, results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Build the validation report object."""
    report: Dict[str, Any] = {
        "schema_version": 1,
        "todo_id": todo_id,
        "created_at": now_iso(),
        "execute": execute,
        "selected_commands": [{"kind": kind, "command": command} for kind, command in selected],
        "results": [dict(item) for item in results],
    }
    report.update(evaluate_results(results) if execute else {"passed": None, "reason": "dry run only; use --execute to run commands"})
    return report


def save_report(root: Path, todo_id: str, report: Mapping[str, Any]) -> Path:
    """Save validation report under project state."""
    directory = root / STATE_DIR / "validation-reports"
    directory.mkdir(parents=True, exist_ok=True)
    safe_todo = todo_id.replace("/", "_")
    path = directory / f"{safe_todo}-{filename_timestamp()}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def record_report_as_todo_evidence(root: Path, todo_id: str, report: Mapping[str, Any]) -> None:
    """Append a saved quality-gate report path to the TODO evidence ledger.

    Import is local so the script still works standalone when copied without the
    package layout. Missing TODOs should fail visibly because evidence without a
    TODO can hide workflow errors.
    """
    try:
        from .todo_manager import add_validation_evidence
    except ImportError:  # pragma: no cover
        from todo_manager import add_validation_evidence  # type: ignore
    saved_to = str(report.get("saved_to", ""))
    passed = report.get("passed")
    selected = report.get("selected_commands", [])
    command_summary = "; ".join(str(item.get("command", "")) for item in selected if isinstance(item, Mapping) and item.get("command"))
    summary = f"quality_gate report: {saved_to}; passed={passed}; execute={report.get('execute')}"
    add_validation_evidence(
        root,
        todo_id,
        summary,
        command=command_summary or None,
        metadata={
            "source": "quality_gate",
            "saved_to": saved_to,
            "passed": passed,
            "execute": report.get("execute"),
            "selected_count": len(selected) if isinstance(selected, list) else 0,
            "result_count": len(report.get("results", [])) if isinstance(report.get("results", []), list) else 0,
        },
    )


def run_quality_gate(root: Path, todo_id: str, kinds: Iterable[str], *, execute: bool, timeout: int, record_todo_evidence: bool = False) -> Dict[str, Any]:
    """Select, optionally execute, save quality-gate evidence, and optionally link it to the TODO."""
    commands_by_kind = load_commands(root)
    selected = select_commands(commands_by_kind, kinds)
    results: List[Dict[str, Any]] = []
    if execute:
        for kind, command in selected:
            result = run_command(command, root=root, timeout=timeout)
            result["kind"] = kind
            results.append(result)
    report = build_report(todo_id, selected, execute=execute, results=results)
    path = save_report(root, todo_id, report)
    report["saved_to"] = str(path)
    if record_todo_evidence and todo_id != "UNSPECIFIED":
        record_report_as_todo_evidence(root, todo_id, report)
        report["recorded_in_todo"] = True
    return report


def main() -> None:
    """CLI entrypoint for quality-gate command selection and execution."""

    parser = argparse.ArgumentParser(description="Run or print review-driven-development quality gates.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--todo-id", default="UNSPECIFIED")
    parser.add_argument("--kinds", default="test,lint,build", help="Comma-separated command groups")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--record-todo-evidence", action="store_true", help="Append saved report path to the TODO validation evidence ledger")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    kinds = [kind.strip() for kind in args.kinds.split(",") if kind.strip()]
    print(json.dumps(run_quality_gate(root, args.todo_id, kinds, execute=args.execute, timeout=args.timeout, record_todo_evidence=args.record_todo_evidence), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
