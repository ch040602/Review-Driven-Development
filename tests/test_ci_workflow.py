from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_uses_root_skill_paths() -> None:
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "skills/review-driven-development/scripts" not in text
    assert "python -m compileall -q -f scripts" in text
    assert "python scripts/validate_skill.py --skill-dir ." in text
    assert "python scripts/skill_registration.py --repo-root . --validate-only" in text
    assert "python scripts/self_test.py" in text
