#!/usr/bin/env python3
"""Shared constants and tiny helpers for review-driven-development.

This module should stay dependency-free. Other helper scripts import from here.
Codex should extend constants conservatively so existing state files remain compatible.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SKILL_NAME = "review-driven-development"
SCHEMA_VERSION = 1
STATE_DIR = Path(".codex") / SKILL_NAME

PROFILE_FILE = "profile.md"
DEFAULTS_FILE = "defaults.json"
TODOS_FILE = "todos.jsonl"
CRITIC_FINDINGS_FILE = "critic-findings.jsonl"
DECISION_LOG_FILE = "decision-log.md"
REVIEW_LEDGER_FILE = "review-ledger.md"
IMPLEMENTATION_LOG_FILE = "implementation-log.md"
COMMANDS_FILE = "commands.json"
CONTEXT_INVENTORY_FILE = "context-inventory.json"
CONTEXT_CACHE_FILE = "context-cache.json"
CONTEXT_PACK_FILE = "context-pack.md"
CONTEXT_SEMANTIC_INDEX_FILE = "context-semantic-index.json"

TODO_STATUSES = {"pending", "in_progress", "blocked", "completed", "deferred"}
FINDING_SEVERITIES = {"blocker", "high", "medium", "low"}
FINDING_DECISIONS = {"accept", "reject", "defer", "needs_user_input"}
WORKFLOW_PHASES = {
    "intake",
    "preplan",
    "decision",
    "todo_generation",
    "execution",
    "validation",
    "documentation",
    "improvement",
    "repeat",
}

LEDGER_FILES = [
    TODOS_FILE,
    CRITIC_FINDINGS_FILE,
    DECISION_LOG_FILE,
    REVIEW_LEDGER_FILE,
    IMPLEMENTATION_LOG_FILE,
]


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp without microseconds."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_stamp() -> str:
    """Return a compact UTC timestamp for filenames."""

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def project_state_dir(root: str | Path) -> Path:
    """Return the project-local RDD state directory path.

    The caller-provided root is treated as the workflow workspace. This keeps
    monorepo use explicit: pass the package/workspace directory when state must
    be scoped below the Git root.
    """

    return Path(root).expanduser().resolve() / STATE_DIR


def safe_slug(value: str, *, fallback: str = "item") -> str:
    """Create a filesystem-safe lowercase slug.

    The implementation is intentionally small. Codex may replace it with a more
    robust slugifier if Unicode path policy is defined by the target project.
    """

    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-._").lower()
    return text or fallback


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if missing and return it as a resolved Path."""

    directory = Path(path).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def markdown_title_from_filename(filename: str) -> str:
    """Return a human-readable title for a markdown ledger filename."""

    stem = Path(filename).stem.replace("-", " ").replace("_", " ")
    return stem.title()


def csv_line(values: Iterable[str]) -> str:
    """Return a simple comma-separated line for tiny human diagnostics.

    Uses the standard CSV writer so commas, quotes, and newlines round-trip in
    diagnostic output.
    """

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="")
    writer.writerow([str(value) for value in values])
    return buffer.getvalue()
