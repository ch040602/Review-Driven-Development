from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "review-driven-development"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from quality_gate import run_quality_gate  # noqa: E402
from todo_manager import (  # noqa: E402
    add_review_record,
    add_validation_evidence,
    complete_todo_if_ready,
    create_todo,
    get_todo,
    update_documentation_status,
)


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT, text=True, capture_output=True, check=True)


def test_skill_layout_and_scripts_compile() -> None:
    run_cmd("-m", "compileall", "-q", "skills/review-driven-development/scripts")
    out = run_cmd("skills/review-driven-development/scripts/validate_skill.py", "--skill-dir", str(SKILL_DIR)).stdout
    assert "ok: `True`" in out


def test_end_to_end_self_test() -> None:
    out = run_cmd("skills/review-driven-development/scripts/self_test.py").stdout
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["validation_briefs"] >= 1
    assert payload["improvement_briefs"] >= 1


def test_registration_helper_validate_only() -> None:
    out = run_cmd("skills/review-driven-development/scripts/skill_registration.py", "--repo-root", str(REPO_ROOT), "--validate-only").stdout
    assert "VALID:" in out


def prepare_completable_todo(root: Path) -> str:
    todo = create_todo(root, "Harden completion gate", acceptance_criteria=["gate checked"])
    todo_id = todo["todo_id"]
    add_validation_evidence(root, todo_id, "manual validation evidence")
    add_review_record(root, todo_id, summary="independent review completed")
    update_documentation_status(root, todo_id, "updated", targets=["README.md"])
    return todo_id


def test_dry_run_quality_gate_does_not_complete_when_commands_exist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        todo = create_todo(root, "Run real gate", acceptance_criteria=["real command passes"])
        todo_id = todo["todo_id"]
        state_dir = root / ".codex" / "review-driven-development"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "commands.json").write_text(json.dumps({"test": ["python -c \"print('ok')\""], "lint": [], "build": [], "eval": []}), encoding="utf-8")

        run_quality_gate(root, todo_id, ["test"], execute=False, timeout=30, record_todo_evidence=True)
        add_review_record(root, todo_id, summary="independent review completed")
        update_documentation_status(root, todo_id, "updated", targets=["README.md"])

        with pytest.raises(RuntimeError, match="configured quality-gate commands require executed passing quality_gate evidence"):
            complete_todo_if_ready(root, todo_id)

        run_quality_gate(root, todo_id, ["test"], execute=True, timeout=30, record_todo_evidence=True)
        complete_todo_if_ready(root, todo_id)
        assert get_todo(root, todo_id)["status"] == "completed"


def test_unresolved_blocker_or_high_review_finding_blocks_completion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        todo_id = prepare_completable_todo(root)
        add_review_record(root, todo_id, findings=[{
            "severity": "high",
            "claim": "Regression risk unresolved",
            "recommendation": "Add proof before completion",
        }])

        with pytest.raises(RuntimeError, match="unresolved blocker/high review findings"):
            complete_todo_if_ready(root, todo_id)


@pytest.mark.parametrize("decision", ["resolved", "reject", "rejected", "defer", "deferred"])
def test_resolved_rejected_or_deferred_blocker_high_review_finding_allows_completion(decision: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        todo_id = prepare_completable_todo(root)
        add_review_record(root, todo_id, findings=[{
            "severity": "blocker",
            "claim": "Concern handled by main agent decision",
            "decision": decision,
        }])

        complete_todo_if_ready(root, todo_id)
        assert get_todo(root, todo_id)["status"] == "completed"


def test_external_skill_urls_are_consistent_offline() -> None:
    registry = json.loads((REPO_ROOT / "external-skills.json").read_text(encoding="utf-8"))
    external_skills = (SKILL_DIR / "references" / "external-skills.md").read_text(encoding="utf-8")
    external_links = (SKILL_DIR / "references" / "external-skill-links.md").read_text(encoding="utf-8")

    missing = [
        item["url"]
        for item in registry
        if item["url"] not in external_skills or item["url"] not in external_links
    ]
    assert missing == []
