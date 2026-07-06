#!/usr/bin/env python3
"""Stop hook: remind about RDD completion gates."""

from __future__ import annotations

import json
import sys


MESSAGE = "RDD stop check: TODO completion needs validation evidence, independent review notes, docs status, and blocker/high decisions."


def main() -> None:
    print(MESSAGE, file=sys.stderr)
    print(json.dumps({"continue": True}, separators=(",", ":")))


if __name__ == "__main__":
    main()
