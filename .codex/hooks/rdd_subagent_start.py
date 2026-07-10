#!/usr/bin/env python3
"""SubagentStart hook: enforce the route contract carried by the spawn payload."""

from __future__ import annotations

import re
import sys


IMPLEMENTATION_MARKER = re.compile(
    r"(?:contract[\"'\s:=-]+implementation|task[_ -]?kind[\"'\s:=-]+(?:simple-implementation|logic-design))",
    re.IGNORECASE,
)


def main() -> None:
    """Keep unmarked routes critical-only; allow only explicit implementation contracts."""

    payload = sys.stdin.read()
    if IMPLEMENTATION_MARKER.search(payload):
        print(
            "RDD subagent rule: bounded implementation only; stay inside the delegated TODO slice, "
            "preserve main-agent decisions, use tests, and escalate scope/risk uncertainty."
        )
        return
    print(
        "RDD subagent rule: critical-only, no patches, prefer reuse/minimal-change findings, "
        "escalate blocker/high uncertainty."
    )


if __name__ == "__main__":
    main()
