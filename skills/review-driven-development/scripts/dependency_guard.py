#!/usr/bin/env python3
"""Guard against unnecessary new dependencies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Set

DEPENDENCY_FILES = ["package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"]
BLOCKING_MINIMALITY_RUNGS = {"skip", "reuse_existing_code", "stdlib", "native", "installed_dep", "one_line"}


def normalize_dependency_name(spec: str) -> str:
    """Extract a normalized dependency name from a package spec."""

    match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    return match.group(1).lower().replace("_", "-") if match else ""


def dependency_names_from_pyproject(text: str) -> Set[str]:
    """Parse project dependencies from pyproject TOML."""

    import tomllib

    names: Set[str] = set()
    data = tomllib.loads(text or "")
    for item in data.get("project", {}).get("dependencies", []) or []:
        name = normalize_dependency_name(str(item))
        if name:
            names.add(name)
    for group in (data.get("project", {}).get("optional-dependencies", {}) or {}).values():
        for item in group:
            name = normalize_dependency_name(str(item))
            if name:
                names.add(name)
    return names


def dependency_names_from_package_json(text: str) -> Set[str]:
    """Parse dependency names from package.json."""

    data = json.loads(text or "{}")
    names: Set[str] = set()
    for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        names.update((data.get(key) or {}).keys())
    return {name.lower() for name in names}


def dependency_names_from_requirements(text: str) -> Set[str]:
    """Parse dependency names from requirements.txt."""

    names: Set[str] = set()
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        name = normalize_dependency_name(stripped)
        if name:
            names.add(name)
    return names


def dependency_names_from_text(filename: str, text: str) -> Set[str]:
    """Parse dependency names from supported manifest text."""

    base = Path(filename).name
    if base == "pyproject.toml":
        return dependency_names_from_pyproject(text)
    if base == "package.json":
        return dependency_names_from_package_json(text)
    if base == "requirements.txt":
        return dependency_names_from_requirements(text)
    if base == "Cargo.toml":
        return {normalize_dependency_name(line.split("=", 1)[0]) for line in text.splitlines() if "=" in line and not line.lstrip().startswith("[")}
    if base == "go.mod":
        return {fields[0].lower() for fields in (line.split() for line in text.splitlines()) if len(fields) >= 2 and "." in fields[0]}
    if base in {"pom.xml", "build.gradle"}:
        return set(re.findall(r"['\"]([A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+)['\"]", text))
    return set()


def build_dependency_report(
    before_files: Mapping[str, str],
    after_files: Mapping[str, str],
    *,
    minimality_packet: Mapping[str, Any] | None = None,
    decision_log_text: str = "",
) -> Dict[str, Any]:
    """Compare dependency manifests and return guard findings."""

    new_dependencies = []
    for filename in DEPENDENCY_FILES:
        before = dependency_names_from_text(filename, before_files.get(filename, ""))
        after = dependency_names_from_text(filename, after_files.get(filename, ""))
        for dependency in sorted(after - before):
            new_dependencies.append({"file": filename, "dependency": dependency})

    blockers = []
    rung = str((minimality_packet or {}).get("rung", ""))
    if new_dependencies and rung in BLOCKING_MINIMALITY_RUNGS:
        blockers.append(f"new dependency blocked because minimality packet chose {rung}")
    if new_dependencies and "dependency decision" not in decision_log_text.lower():
        blockers.append("new dependency requires decision-log.md dependency decision evidence")
    return {"new_dependencies": new_dependencies, "blockers": blockers}


def read_supported_files(root: Path) -> Dict[str, str]:
    """Read supported manifests that exist under root."""

    files: Dict[str, str] = {}
    for filename in DEPENDENCY_FILES:
        path = root / filename
        if path.exists():
            files[filename] = path.read_text(encoding="utf-8", errors="ignore")
    return files


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Check dependency additions against minimality policy.")
    parser.add_argument("--before-root", required=True)
    parser.add_argument("--after-root", default=".")
    parser.add_argument("--minimality-packet")
    parser.add_argument("--decision-log")
    args = parser.parse_args()

    packet: Mapping[str, Any] = {}
    if args.minimality_packet and Path(args.minimality_packet).exists():
        packet = json.loads(Path(args.minimality_packet).read_text(encoding="utf-8"))
    decision_log = Path(args.decision_log).read_text(encoding="utf-8") if args.decision_log and Path(args.decision_log).exists() else ""
    print(json.dumps(
        build_dependency_report(
            read_supported_files(Path(args.before_root)),
            read_supported_files(Path(args.after_root)),
            minimality_packet=packet,
            decision_log_text=decision_log,
        ),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
