#!/usr/bin/env python3
"""Validate the review-driven-development skill draft."""

from __future__ import annotations

import argparse
import py_compile
from pathlib import Path
from typing import Dict, List

try:
    from .model_router import load_routing_policy
except ImportError:  # pragma: no cover
    from model_router import load_routing_policy  # type: ignore

REQUIRED_FILES = [
    "SKILL.md",
    "references/workflow.md",
    "references/subagent-roles.md",
    "references/model-routing.md",
    "references/model-routing-policy.json",
    "references/minimal-solution-policy.md",
    "references/hook-policy.md",
    "references/internal-skill-map.md",
    "references/external-skill-links.md",
    "references/external-skills.json",
    "references/first-run-questionnaire.md",
    "references/script-contracts.md",
    "references/codex-completion-and-registration.md",
    "references/todo-policy.md",
    "references/documentation-policy.md",
    "references/state-schema.md",
    "references/pro-review.md",
    "scripts/constants.py",
    "scripts/rdd_state.py",
    "scripts/context_inventory.py",
    "scripts/minimal_solution_ladder.py",
    "scripts/diff_budget.py",
    "scripts/dependency_guard.py",
    "scripts/model_router.py",
    "scripts/pro_review.py",
    "scripts/rdd_commands.py",
    "scripts/requirement_analyzer.py",
    "scripts/external_skill_registry.py",
    "scripts/subagent_brief_builder.py",
    "scripts/critic_ledger.py",
    "scripts/todo_manager.py",
    "scripts/quality_gate.py",
    "scripts/doc_sync_check.py",
    "scripts/workflow_runner.py",
    "scripts/self_test.py",
]


def check_required_files(skill_dir: Path) -> List[str]:
    """Return missing required file errors."""

    return [f"missing required file: {rel}" for rel in REQUIRED_FILES if not (skill_dir / rel).exists()]


def check_frontmatter(skill_dir: Path) -> List[str]:
    """Validate basic SKILL.md frontmatter."""

    path = skill_dir / "SKILL.md"
    if not path.exists():
        return ["SKILL.md missing"]
    text = path.read_text(encoding="utf-8")
    errors: List[str] = []
    if not text.startswith("---"):
        errors.append("SKILL.md must start with YAML frontmatter")
    if "name: review-driven-development" not in text:
        errors.append("SKILL.md must include name: review-driven-development")
    if "description:" not in text:
        errors.append("SKILL.md must include description")
    return errors


def check_script_compilation(skill_dir: Path) -> List[str]:
    """Compile every Python script."""

    errors: List[str] = []
    for path in sorted((skill_dir / "scripts").glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"py_compile failed for {path.name}: {exc.msg}")
    return errors


def check_model_routing_policy(skill_dir: Path) -> List[str]:
    """Validate the bundled data-driven model catalog and routing policy."""

    path = skill_dir / "references" / "model-routing-policy.json"
    if not path.exists():
        return ["model-routing-policy.json missing"]
    try:
        load_routing_policy(path)
    except (OSError, ValueError, TypeError) as exc:
        return [f"invalid model routing policy: {exc}"]
    return []


def check_external_links(skill_dir: Path) -> List[str]:
    """Check that external skill links file contains required URLs.

    This is static validation and does not access the network.
    """

    path = skill_dir / "references" / "external-skill-links.md"
    if not path.exists():
        return ["external-skill-links.md missing"]
    text = path.read_text(encoding="utf-8")
    required = [
        "https://developers.openai.com/codex/skills",
        "https://developers.openai.com/codex/subagents",
        "https://github.com/openai/skills",
        "https://github.com/openai/skills/blob/main/skills/.curated/gh-address-comments/SKILL.md",
        "https://github.com/addyosmani/agent-skills/blob/main/skills/source-driven-development/SKILL.md",
        "https://github.com/addyosmani/agent-skills/blob/main/skills/planning-and-task-breakdown/SKILL.md",
        "https://github.com/addyosmani/agent-skills/blob/main/skills/code-review-and-quality/SKILL.md",
    ]
    return [f"missing external link: {url}" for url in required if url not in text]


def check_bilingual_readme(skill_dir: Path) -> List[str]:
    """Check root README if available through parent layout."""

    root = skill_dir.parents[1] if len(skill_dir.parents) >= 2 else skill_dir
    readme = root / "README.md"
    if not readme.exists():
        return []
    text = readme.read_text(encoding="utf-8")
    errors = []
    if "## English" not in text:
        errors.append("README.md should include ## English")
    if "## 한국어" not in text:
        errors.append("README.md should include ## 한국어")
    return errors


def check_optional_tests(skill_dir: Path) -> List[str]:
    """Check that behavioral smoke tests are present in the project package."""

    root = skill_dir.parents[1] if len(skill_dir.parents) >= 2 else skill_dir
    tests_dir = skill_dir / "tests"
    if not tests_dir.exists():
        tests_dir = root / "tests"
    if not tests_dir.exists():
        return ["tests/ directory missing; behavioral smoke tests are recommended"]
    if not any(tests_dir.glob("test_*.py")):
        return ["tests/ exists but has no test_*.py behavioral smoke tests"]
    return []


def validate(skill_dir: Path) -> Dict[str, object]:
    """Run all validation checks."""

    errors: List[str] = []
    errors.extend(check_required_files(skill_dir))
    errors.extend(check_frontmatter(skill_dir))
    errors.extend(check_script_compilation(skill_dir))
    errors.extend(check_model_routing_policy(skill_dir))
    errors.extend(check_external_links(skill_dir))
    errors.extend(check_bilingual_readme(skill_dir))
    errors.extend(check_optional_tests(skill_dir))
    return {"ok": not errors, "skill_dir": str(skill_dir), "errors": errors}


def render_report(report: Dict[str, object]) -> str:
    """Render validation report as Markdown."""

    lines = ["# Skill validation report", "", f"- ok: `{report.get('ok')}`", f"- skill_dir: `{report.get('skill_dir')}`"]
    errors = report.get("errors") or []
    if errors:
        lines.append("\n## Errors")
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines)


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Validate review-driven-development skill layout.")
    parser.add_argument("--skill-dir", default=".")
    args = parser.parse_args()

    report = validate(Path(args.skill_dir).resolve())
    print(render_report(report))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
