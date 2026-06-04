#!/usr/bin/env python3
"""
Skill registration helper for review-driven-development.

Role:
- Validate that a skill folder has a `SKILL.md` with minimal frontmatter.
- Copy or symlink the skill into a Codex-discoverable location.
- Print clear next steps for Codex registration.

Implementation notes:
- Frontmatter parsing is minimal and dependency-free by design.
- Installation supports copy or symlink into explicit Codex-discoverable
  targets; updates to existing installs are opt-in through `--force`.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Dict, List

DEFAULT_SKILL_NAME = "review-driven-development"


def candidate_install_dirs(repo_root: Path) -> Dict[str, Path]:
    """Return common Codex-discoverable install locations."""
    return {
        "repo": repo_root / ".agents" / "skills",
        "user": Path.home() / ".agents" / "skills",
    }


def read_frontmatter(skill_md: Path) -> Dict[str, str]:
    """Read minimal YAML-like frontmatter from SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Missing frontmatter fence in {skill_md}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed frontmatter in {skill_md}")
    data: Dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def validate_skill_folder(skill_dir: Path, expected_name: str = DEFAULT_SKILL_NAME) -> List[str]:
    """Return validation errors for a skill folder."""
    errors: List[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.exists():
        return [f"skill directory does not exist: {skill_dir}"]
    if not skill_md.exists():
        return [f"SKILL.md missing: {skill_md}"]
    try:
        frontmatter = read_frontmatter(skill_md)
    except Exception as exc:  # CLI validation should report parse failures.
        return [str(exc)]
    if frontmatter.get("name") != expected_name:
        errors.append(f"frontmatter name must be {expected_name!r}, got {frontmatter.get('name')!r}")
    if not frontmatter.get("description"):
        errors.append("frontmatter description is required")
    return errors


def install_skill(skill_dir: Path, install_root: Path, *, mode: str = "copy", overwrite: bool = False) -> Path:
    """Install a skill folder by copying or symlinking it."""
    errors = validate_skill_folder(skill_dir)
    if errors:
        raise ValueError("Cannot install skill:\n" + "\n".join(f"- {err}" for err in errors))
    install_root.mkdir(parents=True, exist_ok=True)
    target = install_root / skill_dir.name
    if target.exists() or target.is_symlink():
        if not overwrite:
            raise FileExistsError(f"Target already exists: {target}. Use --overwrite to replace.")
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    if mode == "copy":
        shutil.copytree(skill_dir, target)
    elif mode == "symlink":
        target.symlink_to(skill_dir.resolve(), target_is_directory=True)
    else:
        raise ValueError("mode must be 'copy' or 'symlink'")
    return target


def main() -> None:
    """CLI entrypoint for local skill validation and installation."""

    parser = argparse.ArgumentParser(description="Validate and install the review-driven-development skill.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for .agents/skills target")
    parser.add_argument("--skill-dir", default="skills/review-driven-development", help="Source skill directory")
    parser.add_argument("--scope", choices=["repo", "user"], default="repo")
    parser.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    skill_dir = (repo_root / args.skill_dir).resolve() if not Path(args.skill_dir).is_absolute() else Path(args.skill_dir).resolve()
    errors = validate_skill_folder(skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"VALID: {skill_dir}")
    if args.validate_only:
        return
    target_root = candidate_install_dirs(repo_root)[args.scope]
    target = install_skill(skill_dir, target_root, mode=args.mode, overwrite=args.overwrite)
    print(f"INSTALLED: {target}")
    print("Open Codex from the target repository and run /skills, or restart Codex if the skill does not appear.")


if __name__ == "__main__":
    main()
