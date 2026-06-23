#!/usr/bin/env python3
"""PreToolUse hook: guard high-cost dependency/destructive commands."""

from __future__ import annotations

import json
import re
import sys


def main() -> None:
    payload = sys.stdin.read()
    lowered = payload.lower()
    if re.search(r"\b(pip|npm|pnpm|yarn|cargo|go)\s+(install|add|get)\b", lowered):
        print(json.dumps({"decision": "block", "reason": "Run dependency_guard.py and record decision-log.md evidence before adding dependencies."}))
        return
    if re.search(r"\b(rm\s+-rf|git\s+reset\s+--hard|remove-item\b.*-recurse)\b", lowered):
        print(json.dumps({"decision": "block", "reason": "Destructive commands require explicit user confirmation outside the hook."}))
        return
    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
