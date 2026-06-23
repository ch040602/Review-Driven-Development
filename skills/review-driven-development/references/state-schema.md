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
| `minimality_packet.json` | JSON | Current minimal solution ladder decision |
| `rdd-debt.jsonl` | JSONL | Append-only deferred simplification candidates |
| `context-inventory.json` | JSON | Last project context inventory |
| `context-cache.json` | JSON | Fingerprint metadata for safe inventory/context-pack reuse |
| `context-pack.md` | Markdown | Compact Codex-first project context summary |
| `context-semantic-index.json` | JSON | Bounded lexical/symbol locator index for targeted file lookup |
| `AGENTS.md` marker block | Markdown | Optional repo-local fast-context bootstrap instructions |

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
  "minimalism_level": "full",
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

## Context cache

```json
{
  "schema_version": 1,
  "created_at": "2026-06-05T00:00:00+00:00",
  "strategy": "bounded-file-metadata-fingerprint-plus-compact-context-pack",
  "fingerprint": {
    "algorithm": "sha256:path-size-mtime",
    "digest": "",
    "file_count": 0,
    "newest_mtime": 0,
    "newest_path": "",
    "max_files": 5000
  },
  "inventory_path": ".codex/review-driven-development/context-inventory.json",
  "context_pack_path": ".codex/review-driven-development/context-pack.md",
  "semantic_index_path": ".codex/review-driven-development/context-semantic-index.json",
  "semantic_index_summary": {
    "strategy": "bounded-lexical-symbol-index",
    "file_count": 0,
    "symbol_count": 0,
    "top_terms": []
  },
  "scanned_file_count": 0,
  "primary_languages": [],
  "frameworks": []
}
```

`context-pack.md` is intentionally compact Markdown. Consumers should read it before opening the full inventory or source files.

## Semantic index

```json
{
  "schema_version": 1,
  "created_at": "2026-06-05T00:00:00+00:00",
  "strategy": "bounded-lexical-symbol-index",
  "ranking_backend": "embedding-cosine | sklearn-tfidf | lexical-overlap",
  "embedding": {
    "enabled": true,
    "available": true,
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "vectors": [],
    "error": null
  },
  "file_count": 0,
  "symbol_count": 0,
  "files": [{"path": "src/app.py", "terms": [], "symbols": [], "search_text": "bounded search corpus"}],
  "symbols": [{"name": "Example", "kind": "class", "path": "src/app.py", "line": 1}],
  "terms": {"example": ["src/app.py"]}
}
```

The semantic index is a locator only. It narrows which files Codex should open; it does not replace source inspection. Default ranking uses `scikit-learn` TF-IDF when installed, then lexical overlap. Dense `sentence-transformers` ranking is available only when vectors were built with explicit `--embeddings`.
