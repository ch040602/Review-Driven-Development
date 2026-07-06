#!/usr/bin/env python3
"""Build a minimal-solution packet before TODO generation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

STATE_DIR = Path(".codex") / "review-driven-development"
RUNG_SKIP = "skip"
RUNG_REUSE = "reuse_existing_code"
RUNG_STDLIB = "stdlib"
RUNG_NATIVE = "native"
RUNG_INSTALLED_DEP = "installed_dep"
RUNG_ONE_LINE = "one_line"
RUNG_MINIMAL_CODE = "minimal_code"

STOPWORDS = {
    "add",
    "and",
    "for",
    "from",
    "into",
    "new",
    "of",
    "the",
    "to",
    "with",
}
STDLIB_HINTS = {
    "csv": "csv",
    "json": "json",
    "path": "pathlib",
    "file": "pathlib",
    "http": "urllib",
    "url": "urllib",
    "toml": "tomllib",
    "xml": "xml",
    "subprocess": "subprocess",
    "argparse": "argparse",
}


def tokenize(text: str) -> List[str]:
    """Return simple lowercase tokens useful for reuse matching."""

    expanded = re.sub(r"[_\-/.]", " ", text.lower())
    return [token for token in re.findall(r"[a-zA-Z0-9]+", expanded) if len(token) > 2 and token not in STOPWORDS]


def iter_candidate_files(root: Path, *, limit: int = 250) -> Iterable[Path]:
    """Yield bounded likely source/docs files for reuse checks."""

    skipped = {".git", ".pytest_cache", "__pycache__", ".codex"}
    count = 0
    for path in sorted(root.rglob("*")):
        if count >= limit:
            return
        relative_parts = path.relative_to(root).parts
        if not path.is_file() or any(part in skipped for part in relative_parts):
            continue
        if path.suffix.lower() not in {".py", ".md", ".toml", ".json", ".txt"}:
            continue
        count += 1
        yield path


def rank_reuse_candidates(root: Path, requirement: str, *, top_k: int = 5) -> List[Dict[str, Any]]:
    """Rank existing files by lexical overlap with the requirement."""

    query = set(tokenize(requirement))
    if not query:
        return []
    candidates: List[Dict[str, Any]] = []
    for path in iter_candidate_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:8000]
        except OSError:
            continue
        path_tokens = set(tokenize(rel))
        text_tokens = set(tokenize(text))
        overlap = sorted(query & (path_tokens | text_tokens))
        if overlap:
            candidates.append({"path": rel, "score": len(overlap), "matched_terms": overlap[:8]})
    return sorted(candidates, key=lambda item: (-int(item["score"]), str(item["path"])))[:top_k]


def installed_dependency_names(root: Path) -> List[str]:
    """Return lightweight dependency names from common Python manifests."""

    names: set[str] = set()
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            for item in data.get("project", {}).get("dependencies", []) or []:
                names.add(normalize_dependency_name(str(item)))
            for group in (data.get("project", {}).get("optional-dependencies", {}) or {}).values():
                for item in group:
                    names.add(normalize_dependency_name(str(item)))
        except Exception:
            pass
    requirements = root / "requirements.txt"
    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                names.add(normalize_dependency_name(line))
    return sorted(name for name in names if name)


def normalize_dependency_name(spec: str) -> str:
    """Extract a package-ish name from a dependency spec."""

    match = re.match(r"\s*([A-Za-z0-9_.-]+)", spec)
    return match.group(1).lower().replace("_", "-") if match else ""


def choose_rung(root: Path, requirement: str, reuse_candidates: List[Mapping[str, Any]]) -> Dict[str, str]:
    """Choose the first useful rung in the minimal-solution ladder."""

    lowered = requirement.lower()
    if "really need" in lowered or "necessary" in lowered or "yagni" in lowered:
        return {
            "rung": RUNG_SKIP,
            "decision": "Skip implementation until the need is tied to a current acceptance criterion.",
            "add_when": "Only add work after a concrete acceptance criterion exists.",
        }
    if reuse_candidates:
        target = str(reuse_candidates[0]["path"])
        return {
            "rung": RUNG_REUSE,
            "decision": f"Reuse or extend {target} before adding a second scanner, parser, dependency, or abstraction.",
            "add_when": f"Add new code only if {target} cannot satisfy the TODO with a small local change.",
        }
    for term, module in STDLIB_HINTS.items():
        if term in lowered:
            return {
                "rung": RUNG_STDLIB,
                "decision": f"Use Python stdlib module {module} before adding a dependency.",
                "add_when": f"Add a dependency only if {module} cannot meet documented acceptance criteria.",
            }
    for dependency in installed_dependency_names(root):
        if dependency.replace("-", " ") in lowered or dependency in lowered:
            return {
                "rung": RUNG_INSTALLED_DEP,
                "decision": f"Use already installed dependency {dependency} before adding another package.",
                "add_when": "Add a dependency only after recording why installed dependencies are insufficient.",
            }
    if len(tokenize(requirement)) <= 6:
        return {
            "rung": RUNG_ONE_LINE,
            "decision": "Try a direct one-line or single-call change before adding a helper.",
            "add_when": "Add a helper only after the direct change becomes unclear or duplicated.",
        }
    return {
        "rung": RUNG_MINIMAL_CODE,
        "decision": "Implement the smallest local code path that satisfies the current acceptance criteria.",
        "add_when": "Add abstraction only after repeated use or measured complexity justifies it.",
    }


def build_minimality_packet(root: Path, requirement: str, *, todo_id: str | None = None) -> Dict[str, Any]:
    """Return a minimality packet for the requirement."""

    root = root.resolve()
    reuse_candidates = rank_reuse_candidates(root, requirement)
    choice = choose_rung(root, requirement, reuse_candidates)
    return {
        "todo_id": todo_id or "",
        "requirement": requirement,
        "rung": choice["rung"],
        "decision": choice["decision"],
        "reuse_candidates": reuse_candidates,
        "stdlib_candidates": [module for term, module in STDLIB_HINTS.items() if term in requirement.lower()],
        "installed_dependencies": installed_dependency_names(root),
        "skipped": ["new parser", "new dependency", "new abstraction"],
        "add_when": choice["add_when"],
    }


def save_minimality_packet(root: Path, packet: Mapping[str, Any], *, path: Path | None = None) -> Path:
    """Save a minimality packet under RDD state."""

    target = path or (root / STATE_DIR / "minimality_packet.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Build an RDD minimal-solution packet.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--requirement", required=True)
    parser.add_argument("--todo-id")
    parser.add_argument("--output")
    args = parser.parse_args()

    packet = build_minimality_packet(Path(args.root), args.requirement, todo_id=args.todo_id)
    path = save_minimality_packet(Path(args.root), packet, path=Path(args.output) if args.output else None)
    print(json.dumps({"packet_path": str(path), "packet": packet}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
