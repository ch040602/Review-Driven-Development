#!/usr/bin/env python3
"""
Context inventory helper for review-driven-development.

Role:
- Inspect a project tree before planning.
- Detect source languages, Markdown docs, tests, build files, and data files.
- Save `.codex/review-driven-development/context-inventory.json`.
- Recommend critical-only subagent roles.

Extension notes:
- Scanning is bounded and skips common generated directories.
- Dependency graph extraction and deeper package-version analysis remain
  optional project-specific extensions.
- CSV schema sampling is delegated to `data_profile.py`.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

STATE_DIR = Path(".codex") / "review-driven-development"
LANG_BY_EXT = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript/react", ".ts": "typescript", ".tsx": "typescript/react",
    ".java": "java", ".kt": "kotlin", ".swift": "swift", ".go": "go", ".rs": "rust", ".rb": "ruby",
    ".php": "php", ".cs": "csharp", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c",
    ".h": "c/cpp header", ".hpp": "c/cpp header", ".sql": "sql", ".r": "r", ".ipynb": "notebook",
}
DOC_EXTS = {".md", ".mdx", ".rst", ".txt"}
DATA_EXTS = {".csv", ".tsv", ".jsonl", ".parquet", ".xlsx", ".xls", ".ndjson", ".log"}
TEST_HINTS = ("test", "spec", "__tests__", "tests")
BUILD_FILES = {
    "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json", "pyproject.toml", "requirements.txt",
    "Pipfile", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Makefile", "Dockerfile",
    "docker-compose.yml", "compose.yml", "tsconfig.json", "vite.config.ts", "next.config.js",
}
SKIP_DIRS = {".git", ".codex", "node_modules", ".venv", "venv", "dist", "build", "target", ".next", ".cache", "coverage", ".pytest_cache", "__pycache__"}


def now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def should_skip(path: Path) -> bool:
    """Return True if any path component should be skipped."""
    return any(part in SKIP_DIRS for part in path.parts)


def iter_files(root: Path, max_files: int) -> Iterable[Path]:
    """Yield files under root with a hard scan cap."""
    count = 0
    for path in root.rglob("*"):
        try:
            rel_for_skip = path.relative_to(root)
        except ValueError:
            rel_for_skip = path
        if should_skip(rel_for_skip):
            continue
        if path.is_file():
            yield path
            count += 1
            if count >= max_files:
                return


def classify_file(file_path: Path, root: Path) -> Dict[str, Any]:
    """Classify one file for planning and critic selection."""
    rel = str(file_path.relative_to(root))
    ext = file_path.suffix.lower()
    name = file_path.name
    lowered = rel.lower()
    return {
        "path": rel,
        "extension": ext,
        "language": LANG_BY_EXT.get(ext),
        "is_source": ext in LANG_BY_EXT,
        "is_doc": ext in DOC_EXTS or name.upper() == "AGENTS.MD" or name.upper().startswith("README"),
        "is_data": ext in DATA_EXTS,
        "is_test": any(hint in lowered for hint in TEST_HINTS),
        "is_build_file": name in BUILD_FILES,
    }


def collect_classified_files(root: Path, max_files: int) -> List[Dict[str, Any]]:
    """Return classified file metadata."""
    return [classify_file(path, root) for path in iter_files(root, max_files=max_files)]


def count_languages(classified: Iterable[Mapping[str, Any]]) -> Counter[str]:
    """Count detected source languages."""
    counts: Counter[str] = Counter()
    for item in classified:
        if item.get("language"):
            counts[str(item["language"])] += 1
    return counts


def group_paths(classified: Iterable[Mapping[str, Any]]) -> Dict[str, List[str]]:
    """Group paths into source/doc/data/test/build categories."""
    grouped: Dict[str, List[str]] = defaultdict(list)
    for item in classified:
        path = str(item["path"])
        if item.get("is_source"):
            grouped["source_files"].append(path)
        if item.get("is_doc"):
            grouped["docs"].append(path)
        if item.get("is_data"):
            grouped["data_files"].append(path)
        if item.get("is_test"):
            grouped["tests"].append(path)
        if item.get("is_build_file"):
            grouped["build_files"].append(path)
    return grouped


def read_text_snippet(path: Path, max_chars: int = 2000) -> str:
    """Read a small UTF-8 snippet, returning empty string for binary/failed reads."""
    try:
        return path.read_text(encoding="utf-8")[:max_chars]
    except (UnicodeDecodeError, OSError):
        return ""


def collect_doc_snippets(root: Path, docs: Iterable[str], max_docs: int = 20, max_chars: int = 2000) -> Dict[str, str]:
    """Collect snippets from key Markdown/spec files."""
    snippets: Dict[str, str] = {}
    for rel in list(docs)[:max_docs]:
        snippets[rel] = read_text_snippet(root / rel, max_chars=max_chars)
    return snippets


def infer_frameworks(root: Path, grouped: Mapping[str, List[str]]) -> List[str]:
    """Infer likely frameworks from manifests and build files.

    Manifest parsing is intentionally shallow and bounded. It checks exact
    manifest files wherever they appear in the scanned tree.
    """
    frameworks: List[str] = []
    build_files = list(grouped.get("build_files", []))
    for rel in build_files:
        name = Path(rel).name
        if name == "package.json":
            package_text = read_text_snippet(root / rel, max_chars=12000).lower()
            for marker, framework in [("next", "nextjs"), ("react", "react"), ("vite", "vite"), ("vue", "vue"), ("svelte", "svelte"), ("express", "express")]:
                if marker in package_text:
                    frameworks.append(framework)
        elif name == "pyproject.toml":
            pyproject = read_text_snippet(root / rel, max_chars=12000).lower()
            for marker, framework in [("fastapi", "fastapi"), ("django", "django"), ("flask", "flask"), ("pandas", "pandas"), ("pytest", "pytest")]:
                if marker in pyproject:
                    frameworks.append(framework)
        elif name == "requirements.txt":
            requirements = read_text_snippet(root / rel, max_chars=12000).lower()
            for marker, framework in [("fastapi", "fastapi"), ("django", "django"), ("flask", "flask"), ("pandas", "pandas"), ("pytest", "pytest")]:
                if marker in requirements:
                    frameworks.append(framework)
    build_names = {Path(rel).name for rel in build_files}
    if "go.mod" in build_names:
        frameworks.append("go-module")
    if "Cargo.toml" in build_names:
        frameworks.append("rust-cargo")
    return sorted(set(frameworks))


def choose_recommended_critics(inventory: Mapping[str, Any]) -> List[str]:
    """Choose critic roles based on the inventory."""
    critics = [
        "requirements-critic",
        "language-runtime-critic",
        "architecture-critic",
        "existing-code-reuse-refactor-critic" if inventory.get("has_existing_code") else "greenfield-scope-critic",
        "test-tdd-critic",
        "documentation-critic",
    ]
    if inventory.get("requires_data_critic"):
        critics.append("data-csv-critic")
    if inventory.get("frameworks"):
        critics.append("source-driven-framework-critic")
    return critics


def build_inventory(root: Path, max_files: int = 5000, include_snippets: bool = True) -> Dict[str, Any]:
    """Build the full project context inventory."""
    classified = collect_classified_files(root, max_files=max_files)
    language_counts = count_languages(classified)
    grouped = group_paths(classified)
    data: Dict[str, Any] = {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": str(root),
        "scanned_file_count": len(classified),
        "language_counts": dict(language_counts),
        "primary_languages": [lang for lang, _ in language_counts.most_common(5)],
        "frameworks": infer_frameworks(root, grouped),
        "docs": grouped.get("docs", [])[:500],
        "data_files": grouped.get("data_files", [])[:500],
        "tests": grouped.get("tests", [])[:500],
        "build_files": grouped.get("build_files", [])[:100],
        "source_files_sample": grouped.get("source_files", [])[:500],
        "requires_data_critic": bool(grouped.get("data_files")),
        "has_existing_code": bool(grouped.get("source_files")),
        "has_tests": bool(grouped.get("tests")),
    }
    if include_snippets:
        data["doc_snippets"] = collect_doc_snippets(root, data["docs"])
    data["recommended_critics"] = choose_recommended_critics(data)
    return data


def summarize_inventory(data: Mapping[str, Any]) -> str:
    """Return a human-readable summary for prompts and briefs."""
    return "\n".join([
        f"Root: {data.get('root')}",
        f"Primary languages: {', '.join(data.get('primary_languages', [])) or 'none detected'}",
        f"Frameworks: {', '.join(data.get('frameworks', [])) or 'none detected'}",
        f"Existing code: {data.get('has_existing_code')}",
        f"Tests detected: {data.get('has_tests')}",
        f"Data critic required: {data.get('requires_data_critic')}",
        f"Docs: {len(data.get('docs', []))}",
        f"Build files: {', '.join(data.get('build_files', [])[:10])}",
    ])


def save_inventory(root: Path, data: Mapping[str, Any]) -> Path:
    """Save context inventory under project state."""
    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "context-inventory.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_inventory(root: Path) -> Dict[str, Any] | None:
    """Load saved context inventory if it exists.

    Returns None when the saved schema is incompatible or when a scanned
    project file is newer than the inventory file.
    """
    path = root / STATE_DIR / "context-inventory.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("schema_version") != 1:
        return None
    inventory_mtime = path.stat().st_mtime
    max_files = int(data.get("scanned_file_count") or 5000)
    for file_path in iter_files(root, max_files=max(max_files, 1)):
        try:
            if file_path.stat().st_mtime > inventory_mtime:
                return None
        except OSError:
            return None
    return data


def main() -> None:
    """CLI entrypoint for context inventory generation."""

    parser = argparse.ArgumentParser(description="Build project context inventory for review-driven-development.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--no-snippets", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    data = build_inventory(root, max_files=args.max_files, include_snippets=not args.no_snippets)
    if args.save:
        data = dict(data)
        data["saved_to"] = str(save_inventory(root, data))
    print(summarize_inventory(data) if args.summary else json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
