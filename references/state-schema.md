# State schema

All state lives under:

```text
.codex/review-driven-development/
```

## Files

| File | Type | Purpose |
|---|---|---|
| `profile.md` | Markdown | Exact first-run answers and assumptions |
| `defaults.json` | JSON | Parsed defaults used silently on later runs |
| `todos.jsonl` | JSONL | Active TODO lifecycle events plus compact completed stubs |
| `critic-findings.jsonl` | JSONL | Append-only critical findings and decisions |
| `decision-log.md` | Markdown | Human-readable main-agent decisions |
| `review-ledger.md` | Markdown | Critic/review/validation summaries |
| `implementation-log.md` | Markdown | Completed TODO evidence and documentation status |
| `commands.json` | JSON | test/lint/build/eval command groups |
| `minimality_packet.json` | JSON | Current minimal solution ladder decision |
| `rdd-debt.jsonl` | JSONL | Append-only deferred simplification candidates |
| `todo_archive/` | Directory | Completed TODO event-history archives and manifests |
| `context-inventory.json` | JSON | Last project context inventory |
| `context-cache.json` | JSON | Fingerprint metadata for safe inventory/context-pack reuse |
| `context-pack.md` | Markdown | Compact Codex-first project context summary |
| `context-semantic-index.json` | JSON | Bounded lexical/symbol locator index for targeted file lookup |
| `project-structure-completeness.md` | Markdown | Durable current folder structure, inferred roles, completeness checks, gaps, and review focus |
| `project-structure-completeness.json` | JSON | Machine-readable companion for Pro review and automation |
| `AGENTS.md` marker block | Markdown | Optional repo-local fast-context bootstrap instructions |
| `pro-review/` | Directory | Optional ChatGPT Pro review packets, raw responses, extracted TODO candidates, and import evidence |

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

## Project structure completeness

`project-structure-completeness.md` and `project-structure-completeness.json` are refreshed by every RDD context sync. They summarize:

- current folder structure by build/docs/tests/data/source categories
- inferred responsibility roles from the role map
- reuse candidates
- heuristic completeness score and missing checks
- review focus for Codex and ChatGPT Pro feedback

The score is a triage heuristic only; it does not prove production readiness. Pro review packets should attach the Markdown file when present and include the JSON-derived score in `context.md`/`context.yaml`.

## Pro review round

```text
pro-review/<timestamp>-round-001/context.md
pro-review/<timestamp>-round-001/context.yaml
pro-review/<timestamp>-round-001/prompt.md
pro-review/<timestamp>-round-001/agbrowse-result.json
pro-review/<timestamp>-round-001/response.md
pro-review/<timestamp>-round-001/todo-candidates.json
```

`todo-candidates.json` should contain:

```json
{
  "summary": "",
  "todos": [
    {
      "title": "",
      "rationale": "",
      "risk": "blocker | high | medium | low",
      "acceptance_criteria": [],
      "expected_files": [],
      "source_refs": []
    }
  ]
}
```

Completed TODOs are archived by default when `todo_manager.py complete <id>`
runs. Archived completed TODOs keep a compact active-ledger stub:

```json
{
  "schema_version": 1,
  "created_at": "2026-06-03T00:00:00+00:00",
  "event": "archive_stub",
  "todo_id": "RDD-T-00000000",
  "status": "completed",
  "title": "Completed TODO title",
  "archived": true,
  "archive_path": ".codex/review-driven-development/todo_archive/completed-20260603T000000Z.jsonl",
  "archived_event_count": 5,
  "completion_created_at": "2026-06-03T00:00:00+00:00"
}
```

Consumers should treat `archive_stub` as terminal completed state and open the
archive file only when detailed historical evidence is needed. The CLI `list`
command omits completed stubs unless `--include-completed` is provided.
