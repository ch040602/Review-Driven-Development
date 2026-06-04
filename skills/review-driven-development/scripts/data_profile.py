#!/usr/bin/env python3
"""
Data profiling helper for the `review-driven-development` data/CSV critic.

This module provides lightweight, dependency-free profiling for CSV/TSV/JSONL
files so a separate critical subagent can challenge data assumptions after each
TODO or before a data-analysis implementation. It intentionally avoids heavy
analytics dependencies; Codex may extend it with pandas, polars, or SQL tooling
when the target project allows those dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

STATE_DIR = Path(".codex") / "review-driven-development"
TEXT_DATA_EXTS = {".csv", ".tsv", ".jsonl", ".ndjson"}


def now_iso() -> str:
    """Return a stable UTC timestamp for data reports."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def detect_dialect(path: Path) -> Dict[str, Any]:
    """Detect basic delimiter/format hints for a text data file.

    Baseline implementation:
    - Uses file extension for CSV/TSV/JSONL.

    Codex completion notes:
    - Add `csv.Sniffer` with guarded fallbacks.
    - Detect encoding and BOM.
    - Record confidence and sample bytes.
    """

    ext = path.suffix.lower()
    if ext == ".tsv":
        return {"format": "delimited", "delimiter": "\t"}
    if ext in {".jsonl", ".ndjson"}:
        return {"format": "jsonl"}
    return {"format": "delimited", "delimiter": ","}


def iter_delimited_rows(path: Path, *, delimiter: str, max_rows: int) -> Iterable[Dict[str, str]]:
    """Yield rows from a CSV/TSV-like file up to `max_rows`.

    Codex completion notes:
    - Add encoding fallback and bad-line reporting.
    - Preserve raw row numbers for diagnostics.
    """

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for index, row in enumerate(reader):
            if index >= max_rows:
                break
            yield {key: value for key, value in row.items()}


def iter_jsonl_rows(path: Path, *, max_rows: int) -> Iterable[Dict[str, Any]]:
    """Yield JSON objects from a JSONL/NDJSON file up to `max_rows`."""

    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index >= max_rows:
                break
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                yield value
            else:
                yield {"_value": value}


def profile_rows(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Profile rows for schema, missing values, simple uniqueness, and examples.

    Current implementation is intentionally lightweight.

    Codex completion notes:
    - Add numeric type inference, min/max/mean, datetime parsing, outlier flags,
      duplicate row detection, and leakage checks.
    - Add privacy redaction for sensitive-looking values.
    """

    row_count = 0
    columns: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    non_empty: Counter[str] = Counter()
    examples: Dict[str, List[str]] = {}
    unique_samples: Dict[str, set[str]] = {}

    for row in rows:
        row_count += 1
        for key, value in row.items():
            column = str(key)
            columns[column] += 1
            text = "" if value is None else str(value)
            if text == "":
                missing[column] += 1
            else:
                non_empty[column] += 1
                examples.setdefault(column, [])
                if len(examples[column]) < 3 and text not in examples[column]:
                    examples[column].append(text[:120])
                unique_samples.setdefault(column, set())
                if len(unique_samples[column]) < 1000:
                    unique_samples[column].add(text)

    return {
        "sampled_rows": row_count,
        "columns": sorted(columns.keys()),
        "column_presence": dict(columns),
        "missing_counts": dict(missing),
        "non_empty_counts": dict(non_empty),
        "unique_sample_counts": {key: len(value) for key, value in unique_samples.items()},
        "examples": examples,
    }


def profile_data_file(path: Path, *, max_rows: int = 1000) -> Dict[str, Any]:
    """Profile one supported data file.

    The returned report is input for `data-csv-critic`, not a final analysis.
    """

    dialect = detect_dialect(path)
    if dialect["format"] == "jsonl":
        rows = iter_jsonl_rows(path, max_rows=max_rows)
    else:
        rows = iter_delimited_rows(path, delimiter=str(dialect["delimiter"]), max_rows=max_rows)
    profile = profile_rows(rows)
    return {
        "path": str(path),
        "created_at": now_iso(),
        "dialect": dialect,
        "profile": profile,
        "critic_prompts": [
            "Check whether required columns are missing or silently renamed.",
            "Check whether missing values or duplicates affect correctness.",
            "Check whether sample size is enough for the claimed analysis.",
            "Check whether target/label leakage is possible.",
            "Check whether encoding, delimiter, or type inference could be wrong.",
        ],
    }


def discover_data_files(root: Path, *, max_files: int = 500) -> List[Path]:
    """Discover lightweight text data files under `root`.

    Codex completion notes:
    - Reuse `context_inventory` output when available.
    - Add file size caps and explicit opt-in for large files.
    """

    found: List[Path] = []
    for path in root.rglob("*"):
        if any(part in {".git", "node_modules", ".venv", "venv"} for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_DATA_EXTS:
            found.append(path)
            if len(found) >= max_files:
                break
    return found


def build_data_profile_report(root: Path, files: Optional[List[Path]] = None, *, max_rows: int = 1000) -> Dict[str, Any]:
    """Build a data profile report for one or more files."""

    selected = files if files is not None else discover_data_files(root)
    reports = []
    errors = []
    for path in selected:
        try:
            reports.append(profile_data_file(path, max_rows=max_rows))
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append({"path": str(path), "error": type(exc).__name__, "message": str(exc)})
    return {
        "schema_version": 1,
        "created_at": now_iso(),
        "root": str(root),
        "files_profiled": [str(path) for path in selected],
        "reports": reports,
        "errors": errors,
        "critic_note": "Data critic must challenge assumptions; this profile is evidence only.",
    }


def save_report(root: Path, report: Mapping[str, Any]) -> Path:
    """Persist a data profile report under project state."""

    directory = root / STATE_DIR / "data-reports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"data-profile-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    """CLI entrypoint for data profiling."""

    parser = argparse.ArgumentParser(description="Build lightweight data profile reports for RDD critics.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--file", action="append", default=[], help="Specific file to profile. Can be repeated.")
    parser.add_argument("--max-rows", type=int, default=1000)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = [Path(item).expanduser().resolve() for item in args.file] if args.file else None
    report = build_data_profile_report(root, files, max_rows=args.max_rows)
    if args.save:
        report["saved_to"] = str(save_report(root, report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
