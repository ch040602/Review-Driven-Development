#!/usr/bin/env python3
"""End-to-end smoke test for the review-driven-development helper workflow.

This uses only the standard library and local helper scripts. It validates the
state/TODO/critic/workflow path that static `compileall` checks cannot cover.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

try:
    from .critic_ledger import append_finding, create_finding, decide_finding
    from .quality_gate import run_quality_gate
    from .rdd_state import initialize_project_state
    from .todo_manager import add_review_record, complete_todo_if_ready, get_todo, update_documentation_status
    from .workflow_runner import run_once, run_validation_phase, run_documentation_phase, run_improvement_phase
except ImportError:  # pragma: no cover
    from critic_ledger import append_finding, create_finding, decide_finding  # type: ignore
    from quality_gate import run_quality_gate  # type: ignore
    from rdd_state import initialize_project_state  # type: ignore
    from todo_manager import add_review_record, complete_todo_if_ready, get_todo, update_documentation_status  # type: ignore
    from workflow_runner import run_once, run_validation_phase, run_documentation_phase, run_improvement_phase  # type: ignore


def assert_true(condition: bool, message: str) -> None:
    """Raise AssertionError with a clear message."""

    if not condition:
        raise AssertionError(message)


def run_self_test() -> Dict[str, Any]:
    """Run a full non-destructive workflow smoke test and return evidence."""

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Smoke project\n", encoding="utf-8")

        first = run_once(root, "간단한 CLI 기능을 TDD로 구현")
        assert_true("first_run" in first, "first run should ask for defaults before planning")
        initialize_project_state(root, "한국어, 문서화 한국어, TDD 우선", force=False)

        finding = append_finding(root, create_finding(
            role="test-tdd-critic",
            phase="preplan",
            claim="Acceptance test is missing",
            risk="Regression may not be detected",
            severity="high",
            recommendation="Add a regression test before implementation",
            check="pytest passes or explicit validation evidence is recorded",
        ))
        decide_finding(root, finding["finding_id"], "accept", "Required for TODO evidence gate")

        planned = run_once(root, "continue")
        assert_true("preplan" in planned, "preplan briefs should be created after defaults exist")
        assert_true("todo_generation" in planned, "accepted findings should become TODOs")
        assert_true("execution" in planned and planned["execution"].get("active_todo"), "one TODO should start")
        assert_true("validation" not in planned, "validation must not run before implementation")
        assert_true("improvement" not in planned, "improvement must not run before implementation")

        todo_id = planned["execution"]["active_todo"]["todo_id"]
        report = run_quality_gate(root, todo_id, ["test", "lint", "build"], execute=False, timeout=60, record_todo_evidence=True)
        assert_true(Path(report["saved_to"]).exists(), "quality gate report should be saved")

        validation = run_validation_phase(root, todo_id)
        assert_true(validation["brief_paths"], "validation critic briefs should be written")
        add_review_record(root, todo_id, subagent="validation-runner-critic", summary="Smoke review completed with no blocker/high findings.")

        documentation = run_documentation_phase(root, todo_id, ["README.md"])
        assert_true(Path(documentation["doc_report"]).exists(), "documentation report should be saved")
        update_documentation_status(root, todo_id, "updated", targets=["README.md", "implementation-log.md"])

        improvement = run_improvement_phase(root, todo_id, "Smoke improvement critique")
        assert_true(improvement["brief_paths"], "improvement critic briefs should be written")

        complete_todo_if_ready(root, todo_id)
        final_todo = get_todo(root, todo_id)
        assert_true(final_todo["status"] == "completed", "TODO should complete after evidence/review/docs gates")

        return {
            "ok": True,
            "todo_id": todo_id,
            "state_dir": str(root / ".codex" / "review-driven-development"),
            "quality_report": report["saved_to"],
            "validation_briefs": len(validation["brief_paths"]),
            "improvement_briefs": len(improvement["brief_paths"]),
        }


def main() -> None:
    """CLI entrypoint."""

    print(json.dumps(run_self_test(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
