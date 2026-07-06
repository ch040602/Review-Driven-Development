#!/usr/bin/env python3
"""Critical finding and decision ledger helper."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

try:
    from .constants import (
        CRITIC_FINDINGS_FILE,
        DECISION_LOG_FILE,
        FINDING_DECISIONS,
        FINDING_SEVERITIES,
        STATE_DIR,
        utc_now,
    )
except ImportError:  # pragma: no cover
    from constants import (  # type: ignore
        CRITIC_FINDINGS_FILE,
        DECISION_LOG_FILE,
        FINDING_DECISIONS,
        FINDING_SEVERITIES,
        STATE_DIR,
        utc_now,
    )


def findings_path(root: Path) -> Path:
    """Return and initialize the findings JSONL path."""

    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / CRITIC_FINDINGS_FILE
    path.touch(exist_ok=True)
    return path


def normalize_severity(value: str) -> str:
    """Normalize severity to allowed values."""

    value = (value or "medium").strip().lower()
    return value if value in FINDING_SEVERITIES else "medium"


def normalize_decision(value: str) -> str:
    """Normalize main-agent decision to allowed values."""

    value = (value or "defer").strip().lower()
    return value if value in FINDING_DECISIONS else "defer"


def create_finding(
    *,
    role: str,
    phase: str,
    claim: str,
    risk: str = "",
    severity: str = "medium",
    recommendation: str = "",
    missing_evidence: str = "",
    check: str = "",
    todo_id: Optional[str] = None,
    source_refs: Optional[Sequence[Mapping[str, Any] | str]] = None,
) -> Dict[str, Any]:
    """Create a normalized finding record.

    `source_refs` may contain strings or dictionaries describing files, line
    ranges, command outputs, review comments, datasets, or other evidence.
    """

    normalized_refs: List[Dict[str, Any]] = []
    for ref in source_refs or []:
        if isinstance(ref, Mapping):
            normalized_refs.append(dict(ref))
        else:
            normalized_refs.append({"ref": str(ref)})
    return {
        "schema_version": 1,
        "finding_id": f"RDD-F-{uuid.uuid4().hex[:10]}",
        "created_at": utc_now(),
        "role": role,
        "phase": phase,
        "todo_id": todo_id,
        "severity": normalize_severity(severity),
        "claim": claim,
        "risk": risk,
        "missing_evidence": missing_evidence,
        "recommendation": recommendation,
        "check": check,
        "source_refs": normalized_refs,
        "decision": None,
        "decision_reason": None,
    }


def append_finding(root: Path, finding: Mapping[str, Any]) -> Dict[str, Any]:
    """Append a finding to the JSONL ledger."""

    record = dict(finding)
    with findings_path(root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def read_findings(root: Path) -> List[Dict[str, Any]]:
    """Read finding events from JSONL."""

    records: List[Dict[str, Any]] = []
    for line in findings_path(root).read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def decide_finding(root: Path, finding_id: str, decision: str, reason: str) -> Dict[str, Any]:
    """Append a decision event for a finding.

    This does not rewrite prior lines. It appends an event with the same
    `finding_id`, allowing reconstruction through last-write-wins.
    """

    record = {
        "schema_version": 1,
        "finding_id": finding_id,
        "created_at": utc_now(),
        "event": "decision",
        "decision": normalize_decision(decision),
        "decision_reason": reason,
    }
    append_finding(root, record)
    append_decision_markdown(root, finding_id, record["decision"], reason)
    return record


def reconstruct_findings(events: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Reconstruct current finding state from append-only events."""

    state: Dict[str, Dict[str, Any]] = {}
    for event in events:
        fid = str(event.get("finding_id"))
        merged = dict(state.get(fid, {}))
        merged.update(dict(event))
        state[fid] = merged
    return state


def open_findings(root: Path) -> List[Dict[str, Any]]:
    """Return findings without a final decision."""

    state = reconstruct_findings(read_findings(root))
    return [finding for finding in state.values() if not finding.get("decision")]


def accepted_findings(root: Path) -> List[Dict[str, Any]]:
    """Return findings accepted by the main agent."""

    state = reconstruct_findings(read_findings(root))
    return [finding for finding in state.values() if finding.get("decision") == "accept"]


def _risk_rank(severity: str) -> int:
    return {"blocker": 0, "high": 1, "medium": 2, "low": 3}.get(normalize_severity(severity), 2)


def _dedupe_key(finding: Mapping[str, Any]) -> str:
    text = " ".join(str(finding.get(key, "")) for key in ("claim", "recommendation", "check"))
    return " ".join(text.lower().split())


def _dependency_hints(finding: Mapping[str, Any]) -> List[str]:
    """Extract lightweight dependency hints from finding metadata."""

    dependencies = finding.get("dependencies", [])
    if isinstance(dependencies, list):
        return [str(item) for item in dependencies if str(item).strip()]
    if isinstance(dependencies, str) and dependencies.strip():
        return [dependencies.strip()]
    return []


def findings_to_todo_seeds(findings: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Convert accepted findings into TODO seed dictionaries.

    Seeds are deduplicated by claim/recommendation/check, ordered by risk, and
    carry dependency and acceptance-criteria hints for `todo_manager`.
    """

    seeds: List[Dict[str, Any]] = []
    seen: set[str] = set()
    ordered = sorted((dict(item) for item in findings), key=lambda item: (_risk_rank(str(item.get("severity", "medium"))), str(item.get("created_at", ""))))
    for finding in ordered:
        key = _dedupe_key(finding)
        if key in seen:
            continue
        seen.add(key)
        check = str(finding.get("check") or "Evidence exists for the accepted critique.")
        source_refs = finding.get("source_refs", [])
        seeds.append({
            "title": str(finding.get("recommendation") or finding.get("claim") or "Address accepted finding"),
            "rationale": str(finding.get("risk") or finding.get("claim") or "Accepted critical finding."),
            "risk": str(finding.get("severity") or "medium"),
            "source_finding_id": str(finding.get("finding_id")),
            "acceptance_criteria": [check],
            "dependencies": _dependency_hints(finding),
            "source_refs": source_refs if isinstance(source_refs, list) else [],
        })
    return seeds


def append_decision_markdown(root: Path, finding_id: str, decision: str, reason: str) -> Path:
    """Append a human-readable decision entry."""

    directory = root / STATE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / DECISION_LOG_FILE
    if not path.exists():
        path.write_text("# Decision Log\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## Finding {finding_id}\n\n- timestamp: `{utc_now()}`\n- decision: `{decision}`\n- reason: {reason}\n")
    return path


def main() -> None:
    """CLI entrypoint for basic finding ledger operations."""

    parser = argparse.ArgumentParser(description="Manage critical findings for review-driven-development.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--add-claim")
    parser.add_argument("--role", default="manual-critic")
    parser.add_argument("--phase", default="preplan")
    parser.add_argument("--severity", default="medium")
    parser.add_argument("--decision")
    parser.add_argument("--finding-id")
    parser.add_argument("--reason", default="")
    parser.add_argument("--list-open", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.add_claim:
        print(json.dumps(append_finding(root, create_finding(role=args.role, phase=args.phase, claim=args.add_claim, severity=args.severity)), ensure_ascii=False, indent=2))
        return
    if args.decision and args.finding_id:
        print(json.dumps(decide_finding(root, args.finding_id, args.decision, args.reason), ensure_ascii=False, indent=2))
        return
    if args.list_open:
        print(json.dumps(open_findings(root), ensure_ascii=False, indent=2))
        return
    print(json.dumps(read_findings(root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
