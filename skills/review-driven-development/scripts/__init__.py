"""Shared constants for the review-driven-development helper scripts."""

from __future__ import annotations

from pathlib import Path

SKILL_NAME = "review-driven-development"
STATE_DIR = Path(".codex") / SKILL_NAME
SCHEMA_VERSION = 1
DEFAULT_LEDGER_FILES = (
    "todos.jsonl",
    "decision-log.md",
    "review-ledger.md",
    "implementation-log.md",
)
PUBLIC_STATE_FILES = (
    "profile.md",
    "defaults.json",
    "commands.json",
    "context-inventory.json",
    *DEFAULT_LEDGER_FILES,
)

__all__ = [
    "SKILL_NAME",
    "STATE_DIR",
    "SCHEMA_VERSION",
    "DEFAULT_LEDGER_FILES",
    "PUBLIC_STATE_FILES",
]
