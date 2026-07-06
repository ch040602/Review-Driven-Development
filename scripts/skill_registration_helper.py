#!/usr/bin/env python3
"""Skill registration helper for review-driven-development.

Responsibilities
----------------
- Validate that a skill directory contains the expected files.
- Suggest Codex-supported save locations.
- Copy the skill into a repo/user/admin `.agents/skills` target when requested.

Codex completion notes
----------------------
This helper is intentionally local-file-only. It does not download external
skills. Use `external_skill_registry.py` for explicit links and install hints.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

SKILL_NAME = "review-driven-development"
REQUIRED_FILES = ["SKILL.md"]
RECOMMENDED_DIRS = ["references", "scripts"]


@dataclass
class LayoutReport:
    """Skill layout validation result."""

    skill_dir: str
    exists: bool
    required_files: Dict[str, bool]
    recommended_dirs: Dict[str, bool]
    valid: bool
    notes: List[str]


def validate_skill_layout(skill_dir: Path) -> LayoutReport:
    """Check whether `skill_dir` looks like a Codex skill."""

    required = {name: (skill_dir / name).is_file() for name in REQUIRED_FILES}
    recommended = {name: (skill_dir / name).is_dir() for name in RECOMMENDED_DIRS}
    notes: List[str] = []
    if not skill_dir.exists():
        notes.append("skill directory does not exist")
    if not all(required.values()):
        notes.append("missing required SKILL.md")
    if not all(recommended.values()):
        notes.append("references/ and scripts/ are recommended for this workflow")
    return LayoutReport(
        skill_dir=str(skill_dir),
        exists=skill_dir.exists(),
        required_files=required,
        recommended_dirs=recommended,
        valid=skill_dir.exists() and all(required.values()),
        notes=notes,
    )


def suggest_targets(repo_root: Optional[Path] = None, home: Optional[Path] = None) -> Dict[str, str]:
    """Return Codex-supported skill save targets."""

    home = home or Path.home()
    targets = {
        "user": str(home / ".agents" / "skills" / SKILL_NAME),
        "admin": "/etc/codex/skills/review-driven-development",
    }
    if repo_root:
        targets["repo"] = str(repo_root.resolve() / ".agents" / "skills" / SKILL_NAME)
    else:
        targets["repo"] = "$REPO_ROOT/.agents/skills/review-driven-development"
    return targets


def copy_skill(skill_dir: Path, target_dir: Path, *, overwrite: bool = False) -> Path:
    """Copy the skill directory to a Codex skill target."""

    report = validate_skill_layout(skill_dir)
    if not report.valid:
        raise RuntimeError(f"Invalid skill layout: {report.notes}")
    if target_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Target already exists: {target_dir}. Use --overwrite to replace.")
        shutil.rmtree(target_dir)
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_dir, target_dir)
    return target_dir


def registration_commands(skill_dir: Path) -> str:
    """Return shell commands for manual registration."""

    return f"""# Repo-scoped registration
mkdir -p .agents/skills
cp -R {skill_dir} .agents/skills/{SKILL_NAME}

# User-scoped registration
mkdir -p "$HOME/.agents/skills"
cp -R {skill_dir} "$HOME/.agents/skills/{SKILL_NAME}"

# Then restart Codex if the skill does not appear automatically.
"""


def main() -> None:
    """CLI entrypoint for registration assistance."""

    parser = argparse.ArgumentParser(description="Validate/copy the review-driven-development skill.")
    parser.add_argument("--skill-dir", default="skills/review-driven-development")
    parser.add_argument("--repo-root")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--targets", action="store_true")
    parser.add_argument("--commands", action="store_true")
    parser.add_argument("--copy-to")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if args.validate:
        print(json.dumps(asdict(validate_skill_layout(skill_dir)), ensure_ascii=False, indent=2))
        return
    if args.targets:
        repo_root = Path(args.repo_root).resolve() if args.repo_root else None
        print(json.dumps(suggest_targets(repo_root), ensure_ascii=False, indent=2))
        return
    if args.commands:
        print(registration_commands(skill_dir))
        return
    if args.copy_to:
        print(copy_skill(skill_dir, Path(args.copy_to).resolve(), overwrite=args.overwrite))
        return
    print(registration_commands(skill_dir))


if __name__ == "__main__":
    main()
