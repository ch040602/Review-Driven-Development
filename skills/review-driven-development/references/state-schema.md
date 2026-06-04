# State schema / 영구 상태 schema

All state lives under:

```text
.codex/review-driven-development/
```

## Files

| File | Type | Purpose |
|---|---|---|
| `profile.md` | Markdown | Exact first-run answers and assumptions |
| `defaults.json` | JSON | Parsed defaults used silently on later runs |
| `todos.jsonl` | JSONL | Append-only TODO lifecycle events |
| `critic-findings.jsonl` | JSONL | Append-only critical findings and decisions |
| `decision-log.md` | Markdown | Human-readable main-agent decisions |
| `review-ledger.md` | Markdown | Critic/review/validation summaries |
| `implementation-log.md` | Markdown | Completed TODO evidence and documentation status |
| `commands.json` | JSON | test/lint/build/eval command groups |
| `context-inventory.json` | JSON | Last project context inventory |

## TODO event

```json
{
  "schema_version": 1,
  "created_at": "2026-06-03T00:00:00+00:00",
  "event": "create | status | evidence | review_ref | doc_ref",
  "todo_id": "RDD-T-00000000",
  "title": "",
  "status": "pending | in_progress | blocked | completed | deferred",
  "rationale": "",
  "risk": "blocker | high | medium | low",
  "acceptance_criteria": [],
  "dependencies": [],
  "evidence": [],
  "review_refs": [],
  "doc_refs": []
}
```

Helper scripts may also include backward-compatible nested fields:

```json
{
  "timestamp": "same value as created_at",
  "event_type": "legacy event label",
  "validation": {"commands": [], "evidence": []},
  "documentation": {"required": true, "targets": [], "status": "not_started | updated | not_needed"},
  "review": {"required": true, "subagents": [], "findings": []},
  "expected_files": [],
  "source_finding_id": ""
}
```

Consumers should prefer `event`, `created_at`, `evidence`, `review_refs`, and `doc_refs` when available.

## Finding event

```json
{
  "schema_version": 1,
  "created_at": "2026-06-03T00:00:00+00:00",
  "finding_id": "RDD-F-0000000000",
  "role": "requirements-critic",
  "phase": "preplan | validation | improvement",
  "todo_id": null,
  "severity": "blocker | high | medium | low",
  "claim": "",
  "risk": "",
  "missing_evidence": "",
  "recommendation": "",
  "check": "",
  "decision": "accept | reject | defer | needs_user_input | null",
  "decision_reason": ""
}
```

## Defaults

```json
{
  "schema_version": 1,
  "language": {
    "user_facing": "ko",
    "documentation": "ko",
    "preserve_code_terms": true
  },
  "priority": {
    "completeness_over_speed": true,
    "safety_over_scope": true
  },
  "existing_code_policy": "review_then_reuse",
  "implementation_method": "tdd_first_incremental",
  "source_grounding": true,
  "markdown_context": true,
  "parallel_subagent_policy": "maximize_where_safe",
  "critical_subagents": {
    "preplan": true,
    "validation": true,
    "improvement": true
  },
  "documentation": {
    "always_document_completed_todos": true,
    "adr_for_significant_decisions": true
  },
  "commands": {
    "test": [],
    "lint": [],
    "build": [],
    "eval": []
  }
}
```
