#!/usr/bin/env python3
"""Convenience commands for RDD simplification, audit, debt, gain, and Spark review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

try:
    from .context_inventory import build_inventory
    from .diff_budget import analyze_diff_text, git_diff
    from .workflow_runner import run_spark_review_phase
except ImportError:  # pragma: no cover
    from context_inventory import build_inventory  # type: ignore
    from diff_budget import analyze_diff_text, git_diff  # type: ignore
    from workflow_runner import run_spark_review_phase  # type: ignore

STATE_DIR = Path(".codex") / "review-driven-development"


def state_file(root: Path, name: str) -> Path:
    """Return a path under the RDD state directory."""

    path = root / STATE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_simplify(root: Path) -> Dict[str, Any]:
    """Create a delete-list oriented report for the current diff."""

    report = analyze_diff_text(git_diff(root))
    delete_list = []
    if report["metrics"]["new_classes"] > 0:
        delete_list.append("Review new classes: can a function or existing helper replace them?")
    if report["metrics"]["config_files_added"] > 0:
        delete_list.append("Review new config files: keep only values that actually vary.")
    if report["metrics"]["new_dependencies"] > 0:
        delete_list.append("Run dependency_guard.py before accepting dependency additions.")
    if not delete_list:
        delete_list.append("No automatic delete-list candidates found; run simplification-critic for qualitative review.")
    payload = {"command": "rdd-simplify", "diff_budget": report, "delete_list": delete_list}
    path = state_file(root, "rdd-simplify-report.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["report_path"] = str(path)
    return payload


def run_audit(root: Path) -> Dict[str, Any]:
    """Create a lightweight repo audit for reuse and abstraction hotspots."""

    inventory = build_inventory(root, mode="standard")
    payload = {
        "command": "rdd-audit",
        "reuse_candidates": inventory.get("reuse_candidates", []),
        "recommended_critics": inventory.get("recommended_critics", []),
        "note": "Audit is a locator, not a decision; inspect files before deleting or refactoring.",
    }
    path = state_file(root, "rdd-audit-report.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["report_path"] = str(path)
    return payload


def append_debt(root: Path, title: str, reason: str = "") -> Dict[str, Any]:
    """Append one simplification debt item."""

    path = state_file(root, "rdd-debt.jsonl")
    item = {"title": title, "reason": reason, "status": "open"}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return {"command": "rdd-debt", "debt_path": str(path), "item": item}


def run_gain(root: Path) -> Dict[str, Any]:
    """Report current diff budget as a change-size versus evidence proxy."""

    report = analyze_diff_text(git_diff(root))
    payload = {
        "command": "rdd-gain",
        "diff_budget": report,
        "note": "This reports current change size and blockers only; compare branches externally for LOC/token/time benchmarks.",
    }
    path = state_file(root, "rdd-gain-report.json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["report_path"] = str(path)
    return payload


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="RDD convenience commands.")
    parser.add_argument("command", choices=["simplify", "audit", "debt", "gain", "spark-review"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--todo-id", default="RDD-T-00000000")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--title", default="Simplification candidate")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.command == "simplify":
        result = run_simplify(root)
    elif args.command == "audit":
        result = run_audit(root)
    elif args.command == "debt":
        result = append_debt(root, args.title, args.reason)
    elif args.command == "gain":
        result = run_gain(root)
    else:
        result = run_spark_review_phase(root, args.todo_id, args.prompt or "Fast Spark simplification review.")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
