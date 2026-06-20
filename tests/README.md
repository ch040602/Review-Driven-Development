# Test plan

Use these behavioral checks when extending the helper scripts.

Suggested tests:

- `rdd_state.ensure_state` creates state files without overwriting existing profile/defaults.
- `rdd_state.initialize_project_state` stores exact answers and parsed defaults.
- `todo_manager` enforces one `in_progress` TODO.
- `todo_manager.complete_todo_if_ready` rejects TODOs without evidence, independent review, and docs.
- `context_inventory.build_inventory` detects language, tests, docs, build files, and CSV files.
- `context_inventory.sync_context` writes a reusable cache and compact context pack.
- `context_inventory.sync_context` writes a bounded semantic locator index.
- `context_inventory.search_semantic_index` ranks relevant files with embedding cosine when vectors are available, TF-IDF when available, and lexical fallback when forced.
- `context_inventory.write_bootstrap` injects a marker-managed `AGENTS.md` fast-context block.
- `workflow_runner` exposes `sync`, `overview`, `semantic-index`, `semantic-search`, `bootstrap`, and `commands` phases.
- `quality_gate.run_quality_gate` dry-runs without executing commands.
- `subagent_brief_builder.write_briefs` emits critical-only role briefs.
- `doc_sync_check.build_doc_sync_report` reports documentation targets.
