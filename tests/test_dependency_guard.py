from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT if (REPO_ROOT / "SKILL.md").exists() else REPO_ROOT / "skills" / "review-driven-development"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from dependency_guard import build_dependency_report, dependency_names_from_pyproject  # noqa: E402


def test_dependency_guard_detects_new_pyproject_optional_dependency() -> None:
    before = "[project.optional-dependencies]\nsemantic = [\"scikit-learn>=1.4\"]\n"
    after = "[project.optional-dependencies]\nsemantic = [\"scikit-learn>=1.4\", \"requests>=2\"]\n"

    report = build_dependency_report(
        {"pyproject.toml": before},
        {"pyproject.toml": after},
        minimality_packet={"rung": "stdlib", "decision": "Use urllib from stdlib."},
        decision_log_text="",
    )

    assert dependency_names_from_pyproject(after) >= {"scikit-learn", "requests"}
    assert report["new_dependencies"] == [{"file": "pyproject.toml", "dependency": "requests"}]
    assert any("minimality packet chose stdlib" in blocker for blocker in report["blockers"])


def test_dependency_guard_allows_dependency_with_recorded_decision() -> None:
    report = build_dependency_report(
        {"requirements.txt": ""},
        {"requirements.txt": "rich==13.0\n"},
        minimality_packet={"rung": "minimal-code", "decision": "No stdlib equivalent."},
        decision_log_text="Dependency decision: rich is required for terminal rendering.",
    )

    assert report["new_dependencies"] == [{"file": "requirements.txt", "dependency": "rich"}]
    assert report["blockers"] == []
