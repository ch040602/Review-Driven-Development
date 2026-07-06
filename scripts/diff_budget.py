#!/usr/bin/env python3
"""Measure whether a diff is larger than the TODO justifies."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

DEPENDENCY_FILES = {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"}
CONFIG_SUFFIXES = {".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"}
LOGIC_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".kt", ".cs", ".cpp", ".c", ".h", ".hpp"}


def is_test_path(path: str) -> bool:
    """Return True when a path is clearly a test path."""

    normalized = path.replace("\\", "/").lower()
    return "/test" in normalized or normalized.startswith("test") or "_test." in normalized or normalized.endswith(".test.ts")


def analyze_diff_text(diff_text: str) -> Dict[str, Any]:
    """Return diff-budget metrics, warnings, and blockers for unified diff text."""

    touched: set[str] = set()
    added_files: set[str] = set()
    added_loc = 0
    new_classes = 0
    new_dependencies = 0
    config_files_added = 0
    logic_changed = False
    tests_changed = False

    current_path = ""
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                current_path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                touched.add(current_path)
                if current_path in DEPENDENCY_FILES or Path(current_path).name in DEPENDENCY_FILES:
                    new_dependencies += 1
                if Path(current_path).suffix in LOGIC_SUFFIXES and not is_test_path(current_path):
                    logic_changed = True
                if is_test_path(current_path):
                    tests_changed = True
            continue
        if line.startswith("new file mode") and current_path:
            added_files.add(current_path)
            if Path(current_path).suffix in CONFIG_SUFFIXES:
                config_files_added += 1
        if line.startswith("+") and not line.startswith("+++"):
            stripped = line[1:].strip()
            if not stripped:
                continue
            added_loc += 1
            if re.match(r"(class\s+\w+|export\s+class\s+\w+)", stripped):
                new_classes += 1

    metrics = {
        "touched_files": len(touched),
        "added_loc": added_loc,
        "new_classes": new_classes,
        "new_dependencies": new_dependencies,
        "config_files_added": config_files_added,
        "tests_changed": tests_changed,
        "logic_changed": logic_changed,
    }
    warnings: List[str] = []
    blockers: List[str] = []
    if metrics["touched_files"] > 5:
        warnings.append("touched files exceeds default budget: 5")
    if added_loc > 200:
        warnings.append("added LOC exceeds default budget: 200")
    if new_classes > 2:
        warnings.append("new classes exceeds default budget: 2")
    if new_dependencies >= 1:
        warnings.append("new dependencies require dependency_guard decision evidence")
    if config_files_added > 2:
        warnings.append("config files added exceeds default budget: 2")
    if logic_changed and not tests_changed:
        blockers.append("tests missing while logic files changed")
    return {"metrics": metrics, "warnings": warnings, "blockers": blockers}


def git_diff(root: Path, ref: str = "HEAD") -> str:
    """Return git diff text for root."""

    return subprocess.run(
        ["git", "diff", ref, "--"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    ).stdout


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Check RDD diff budget.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--diff-file")
    args = parser.parse_args()

    diff_text = Path(args.diff_file).read_text(encoding="utf-8") if args.diff_file else git_diff(Path(args.root), args.ref)
    print(json.dumps(analyze_diff_text(diff_text), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
