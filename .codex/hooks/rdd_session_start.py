#!/usr/bin/env python3
"""SessionStart hook: print compact RDD state guidance."""

from __future__ import annotations

from pathlib import Path

STATE = Path(".codex/review-driven-development")
PACK = STATE / "context-pack.md"
print(f"RDD: read {PACK} first when it exists; run context_inventory.py --sync --summary if stale.")
print("RDD: minimalism_level defaults to full; use minimal_solution_ladder.py before TODO generation.")
