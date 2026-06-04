# Test plan

Use these behavioral checks when extending the helper scripts.

Suggested tests:

- `rdd_state.ensure_state` creates state files without overwriting existing profile/defaults.
- `rdd_state.initialize_project_state` stores exact answers and parsed defaults.
- `todo_manager` enforces one `in_progress` TODO.
- `todo_manager.complete_todo_if_ready` rejects TODOs without evidence, independent review, and docs.
- `context_inventory.build_inventory` detects language, tests, docs, build files, and CSV files.
- `quality_gate.run_quality_gate` dry-runs without executing commands.
- `subagent_brief_builder.write_briefs` emits critical-only role briefs.
- `doc_sync_check.build_doc_sync_report` reports documentation targets.
