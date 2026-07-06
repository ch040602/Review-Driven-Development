# Script contracts

This document defines implementation boundaries for the helper scripts. Codex should complete implementation details inside these boundaries instead of changing the workflow contract.

This document defines implementation boundaries for helper scripts. Codex should complete implementation details inside these boundaries without changing the workflow contract.

## Common rules

- Scripts are helpers, not final decision makers.
- All persistent writes stay under `.codex/review-driven-development/` unless the user explicitly asks otherwise.
- Append-only ledgers are not rewritten unless a migration or completed-TODO archive manifest is recorded.
- Validation evidence must be machine-readable and human-reviewable.
- Critical subagent outputs are findings, not decisions.
- External/community skill links must remain explicit and inspect-before-use.
- Public function names in this document should not change without updating this file and `function-scaffold.md`.

## `constants.py`

Purpose: Shared constants, path helpers, timestamp helpers, and tiny formatting utilities.

| Function/class | Intended implementation boundary |
|---|---|
| `utc_now` | Return an ISO-8601 UTC timestamp without microseconds. |
| `utc_stamp` | Return a compact UTC timestamp for filenames. |
| `project_state_dir` | Return the project-local RDD state directory path. |
| `safe_slug` | Create a filesystem-safe lowercase slug. |
| `ensure_directory` | Create a directory if missing and return it as a resolved Path. |
| `markdown_title_from_filename` | Return a human-readable title for a markdown ledger filename. |
| `csv_line` | Return a simple comma-separated line for tiny human diagnostics. |

## `context_inventory.py`

Purpose: Inspect source/docs/tests/build/data context before planning, write reusable cache metadata, create compact context packs, and route critics based on evidence.

| Function/class | Intended implementation boundary |
|---|---|
| `now_iso` | Return a stable UTC timestamp. |
| `should_skip` | Return True if any path component should be skipped. |
| `iter_files` | Yield files under root with a hard scan cap. |
| `classify_file` | Classify one file for planning and critic selection. |
| `collect_classified_files` | Return classified file metadata. |
| `count_languages` | Count detected source languages. |
| `group_paths` | Group paths into source/doc/data/test/build categories. |
| `read_text_snippet` | Read a small UTF-8 snippet, returning empty string for binary/failed reads. |
| `tokenize_for_index` | Return stable high-signal terms for a semantic locator index. |
| `extract_symbols` | Extract shallow function/class/interface symbols from one text file. |
| `split_identifier_terms` | Expand snake/camel/path identifiers into searchable terms. |
| `build_search_text` | Build bounded text used by semantic ranking backends. |
| `sklearn_available` | Return True when scikit-learn semantic ranking can be used. |
| `sentence_transformers_available` | Return True when dense embedding ranking can be used. |
| `encode_embedding_texts` | Encode texts with SentenceTransformers, returning JSON-serializable vectors. |
| `dot_score` | Return cosine score for normalized vectors, or dot-product fallback. |
| `collect_doc_snippets` | Collect snippets from key Markdown/spec files. |
| `prioritize_paths` | Order paths for compact Codex context consumption. |
| `unique_ordered` | Return unique paths while preserving the incoming order. |
| `build_file_fingerprint` | Build a cheap project fingerprint without reading file contents. |
| `build_semantic_index` | Build a bounded lexical/symbol index for quick file location. |
| `summarize_semantic_index` | Return compact semantic index metadata for context packs and cache. |
| `search_semantic_index` | Rank semantic index files for a query using TF-IDF when available. |
| `infer_frameworks` | Infer likely frameworks from manifests and build files. |
| `choose_recommended_critics` | Choose critic roles based on the inventory. |
| `build_inventory` | Build the full project context inventory. |
| `build_context_pack` | Build a compact Markdown pack optimized for quick Codex reference. |
| `summarize_inventory` | Return a human-readable summary for prompts and briefs. |
| `save_inventory` | Save context inventory under project state. |
| `save_context_pack` | Save a compact Markdown context pack for fast Codex loading. |
| `save_context_cache` | Save cache metadata used to reuse inventory and context packs safely. |
| `save_semantic_index` | Save the semantic locator index under project state. |
| `load_inventory` | Load saved context inventory if it exists. |
| `load_context_pack` | Load the compact context pack if present. |
| `load_context_cache` | Load context cache metadata if present and parseable. |
| `load_semantic_index` | Load the semantic locator index if present and parseable. |
| `detect_context_script` | Return the best repo-local context inventory command path. |
| `build_bootstrap_block` | Build an AGENTS.md block that injects fast context instructions. |
| `write_bootstrap` | Insert or replace the RDD fast-context bootstrap block in a repo file. |
| `sync_context` | Reuse valid context cache or rebuild inventory and compact context pack. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `minimal_solution_ladder.py`

Purpose: Build a pre-TODO minimality packet so RDD prefers skip/reuse/stdlib/native/installed dependency/one-line/minimal-code in that order.

| Function/class | Intended implementation boundary |
|---|---|
| `rank_reuse_candidates` | Rank existing files by bounded lexical overlap with the requirement. |
| `installed_dependency_names` | Return lightweight dependency names from Python manifests. |
| `choose_rung` | Select one ladder rung without making a final main-agent decision. |
| `build_minimality_packet` | Return machine-readable minimality evidence. |
| `save_minimality_packet` | Persist the packet under `.codex/review-driven-development/`. |
| `main` | CLI entrypoint; keep writes bounded to the requested packet path/state directory. |

## `diff_budget.py`

Purpose: Detect over-large diffs and missing tests for logic changes.

| Function/class | Intended implementation boundary |
|---|---|
| `analyze_diff_text` | Parse unified diff text and return metrics, warnings, blockers. |
| `git_diff` | Read current git diff for a root/ref. |
| `main` | CLI entrypoint; report only, do not edit files. |

## `dependency_guard.py`

Purpose: Compare dependency manifests before/after and block unjustified additions.

| Function/class | Intended implementation boundary |
|---|---|
| `dependency_names_from_text` | Parse supported manifest formats conservatively. |
| `build_dependency_report` | Return new dependencies and blockers from minimality/decision evidence. |
| `main` | CLI entrypoint; report only, do not edit manifests. |

## `model_router.py`

Purpose: Map critic roles to custom-agent configs and manual spawn plans.

| Function/class | Intended implementation boundary |
|---|---|
| `route_role` | Return role, custom agent, model, sandbox, and escalation metadata. |
| `build_spawn_plan` | Build manual spawn instructions from generated brief paths. |
| `main` | CLI entrypoint; never claim subagents executed. |

## `rdd_commands.py`

Purpose: Provide `rdd-simplify`, `rdd-audit`, `rdd-debt`, `rdd-gain`, and `rdd-spark-review` helper surfaces.

| Function/class | Intended implementation boundary |
|---|---|
| `run_simplify` | Save a current-diff delete-list report. |
| `run_audit` | Save a lightweight repo audit from context inventory. |
| `append_debt` | Append one simplification candidate to `rdd-debt.jsonl`. |
| `run_gain` | Save current diff-budget evidence as a gain proxy. |
| `main` | CLI entrypoint; report or append only, never patch code. |

## `critic_ledger.py`

Purpose: Store critic findings and main-agent accept/reject/defer decisions as an append-only ledger.

| Function/class | Intended implementation boundary |
|---|---|
| `findings_path` | Return and initialize the findings JSONL path. |
| `normalize_severity` | Normalize severity to allowed values. |
| `normalize_decision` | Normalize main-agent decision to allowed values. |
| `create_finding` | Create a normalized finding record. |
| `append_finding` | Append a finding to the JSONL ledger. |
| `read_findings` | Read finding events from JSONL. |
| `decide_finding` | Append a decision event for a finding. |
| `reconstruct_findings` | Reconstruct current finding state from append-only events. |
| `open_findings` | Return findings without a final decision. |
| `accepted_findings` | Return findings accepted by the main agent. |
| `findings_to_todo_seeds` | Convert accepted findings into TODO seed dictionaries. |
| `append_decision_markdown` | Append a human-readable decision entry. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `data_profile.py`

Purpose: Profile CSV/TSV/JSONL files for the data critic and improvement loop.

| Function/class | Intended implementation boundary |
|---|---|
| `now_iso` | Return a stable UTC timestamp for data reports. |
| `detect_dialect` | Detect basic delimiter/format hints for a text data file. |
| `iter_delimited_rows` | Yield rows from a CSV/TSV-like file up to `max_rows`. |
| `iter_jsonl_rows` | Yield JSON objects from a JSONL/NDJSON file up to `max_rows`. |
| `profile_rows` | Profile rows for schema, missing values, simple uniqueness, and examples. |
| `profile_data_file` | Profile one supported data file. |
| `discover_data_files` | Discover lightweight text data files under `root`. |
| `build_data_profile_report` | Build a data profile report for one or more files. |
| `save_report` | Persist a data profile report under project state. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `doc_sync_check.py`

Purpose: Infer documentation targets and create documentation sync evidence for each TODO.

| Function/class | Intended implementation boundary |
|---|---|
| `now_iso` | Return a stable UTC timestamp. |
| `filename_timestamp` | Return timestamp for report filenames. |
| `path_exists` | Check whether a documentation target exists. |
| `discover_docs` | Return found and missing documentation targets. |
| `infer_targets_from_files` | Infer documentation targets from changed files. |
| `load_todo` | Load a materialized TODO from todos.jsonl if available. |
| `infer_targets_for_todo` | Infer documentation targets from TODO metadata and changed files. |
| `build_doc_sync_report` | Build a documentation synchronization report. |
| `save_report` | Save a documentation sync report under project state. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `external_skill_registry.py`

Purpose: Keep external skill names, URLs, phases, and installation hints explicit and machine-readable.

| Function/class | Intended implementation boundary |
|---|---|
| `ExternalSkill` | A skill dependency or recommended external workflow. |
| `all_skills` | Return every external skill entry. |
| `skills_for_phase` | Return skills associated with a phase. |
| `required_skills` | Return skills marked required by the RDD workflow. |
| `find_skill` | Find a skill entry by name, case-insensitive. |
| `install_hints` | Return install commands/hints for selected skill names. |
| `render_markdown` | Render skill entries as Markdown with explicit links and install hints. |
| `as_json` | Render skill entries as JSON. |
| `write_registry` | Write registry to a file as JSON or Markdown. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `quality_gate.py`

Purpose: Run or dry-run configured test/lint/build/eval commands and persist validation reports.

| Function/class | Intended implementation boundary |
|---|---|
| `now_iso` | Return a stable UTC timestamp. |
| `filename_timestamp` | Return timestamp for report filenames. |
| `load_json` | Load JSON if available, otherwise return default. |
| `normalize_commands` | Normalize command mapping into lists for test/lint/build/eval. |
| `load_commands` | Load quality-gate commands from commands.json or defaults.json. |
| `select_commands` | Select commands in stable kind order. |
| `run_command` | Execute a shell command and return bounded evidence. |
| `evaluate_results` | Summarize pass/fail status for executed quality gates. |
| `build_report` | Build the validation report object. |
| `save_report` | Save validation report under project state. |
| `record_report_as_todo_evidence` | Append a saved quality-gate report path to the TODO evidence ledger. |
| `run_quality_gate` | Select, optionally execute, save quality-gate evidence, and optionally link it to the TODO. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `rdd_state.py`

Purpose: Initialize and maintain persistent project defaults, profile, decisions, review summaries, command config, and implementation logs.

| Function/class | Intended implementation boundary |
|---|---|
| `now_iso` | Return a stable UTC timestamp. |
| `filename_timestamp` | Return a filename-safe UTC timestamp. |
| `resolve_root` | Resolve and validate the target project root. |
| `state_path` | Return the persistent state directory path for a project root. |
| `initial_text_for` | Return default content for a new state file. |
| `ensure_state` | Create the state directory and baseline ledger files without overwriting. |
| `read_json` | Read a JSON file; return `default` if absent. |
| `write_json` | Write deterministic UTF-8 JSON with explicit overwrite control. |
| `default_defaults` | Return conservative first-run defaults for the skill. |
| `normalize_language` | Normalize language labels to `ko` or `en`. |
| `merge_preserving_safety` | Merge defaults while preserving destructive-change safety settings. |
| `parse_command_hints` | Extract common test/lint/build/eval commands from free text. |
| `parse_first_run_answers` | Parse first-run answers into durable defaults. |
| `load_defaults` | Load project defaults if initialized. |
| `write_defaults` | Persist parsed defaults. |
| `write_profile` | Persist the exact first-run answer as Markdown. |
| `initialize_project_state` | Initialize profile and defaults together after the first-run questionnaire. |
| `update_defaults` | Update defaults using conservative merge semantics. |
| `append_markdown` | Append a timestamped Markdown section to a state ledger. |
| `append_decision` | Append an accepted/rejected/deferred critique decision. |
| `append_review_summary` | Append a critical subagent review summary. |
| `append_implementation_log` | Append implementation evidence for a completed or blocked TODO. |
| `update_commands` | Write project-specific quality-gate commands. |
| `load_context_inventory` | Load saved context inventory if present. |
| `status` | Return a compact state summary. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `requirement_analyzer.py`

Purpose: Convert a raw prompt and inventory into options, tradeoffs, constraints, and first-run questions.

| Function/class | Intended implementation boundary |
|---|---|
| `Option` | A candidate option with tradeoffs. |
| `RequirementPacket` | Structured packet consumed by planning and critic phases. |
| `summarize_prompt` | Create a compact prompt summary. |
| `extract_constraints` | Extract hard constraints from prompt and Markdown text. |
| `infer_language_options` | Infer plausible implementation languages from inventory. |
| `build_method_options` | Return implementation method options with pros and cons. |
| `build_existing_code_options` | Return reuse/review/refactor/rewrite options. |
| `build_validation_options` | Return validation strategy options. |
| `build_documentation_options` | Return documentation strategy options. |
| `build_first_run_questions` | Build first-run questions based on context. |
| `create_requirement_packet` | Create a structured requirement packet for critic/planning phases. |
| `render_packet_markdown` | Render a first-response packet with pros/cons. |
| `packet_to_dict` | Convert packet dataclasses into plain dictionaries. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `skill_registration.py`

Purpose: Validate and copy/symlink the skill into Codex-discoverable locations.

| Function/class | Intended implementation boundary |
|---|---|
| `candidate_install_dirs` | Return common Codex-discoverable install locations. |
| `read_frontmatter` | Read minimal YAML-like frontmatter from SKILL.md. |
| `validate_skill_folder` | Return validation errors for a skill folder. |
| `install_skill` | Install a skill folder by copying or symlinking it. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `skill_registration_helper.py`

Purpose: Provide additional registration layout checks and manual command generation.

| Function/class | Intended implementation boundary |
|---|---|
| `LayoutReport` | Skill layout validation result. |
| `validate_skill_layout` | Check whether `skill_dir` looks like a Codex skill. |
| `suggest_targets` | Return Codex-supported skill save targets. |
| `copy_skill` | Copy the skill directory to a Codex skill target. |
| `registration_commands` | Return shell commands for manual registration. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `subagent_brief_builder.py`

Purpose: Generate critical-only subagent briefs and decision tables for main-agent review.

| Function/class | Intended implementation boundary |
|---|---|
| `RoleSpec` | Definition of one critical-only subagent role. |
| `now_stamp` | Return timestamp for brief directory names. |
| `get_role_spec` | Return a role spec, with a generic fallback. |
| `load_inventory` | Load saved context inventory if present. |
| `role_list_for_phase` | Return critic roles for a phase using inventory hints. |
| `build_brief` | Build a Markdown prompt for one critical-only subagent. |
| `write_briefs` | Write critical-only briefs for one phase. |
| `write_spawn_plan` | Write a manual custom-agent spawn plan for generated briefs. |
| `parse_findings_placeholder` | Placeholder parser for subagent findings. |
| `build_decision_table` | Create a decision table template for the main agent. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `todo_manager.py`

Purpose: Manage TODO creation, state transitions, review findings, validation evidence, documentation status, and completion gates.

| Function/class | Intended implementation boundary |
|---|---|
| `now_iso` | Return a stable UTC timestamp. |
| `utc_stamp` | Return a compact UTC timestamp for archive filenames. |
| `todos_path` | Return TODO ledger path, creating the parent directory. |
| `todo_archive_dir` | Return completed TODO archive directory, creating it if needed. |
| `read_events` | Read append-only TODO events. |
| `deep_merge` | Merge nested dictionaries while replacing non-dict values. |
| `current_state` | Materialize current TODO state from ledger events. |
| `validate_status` | Raise if status is invalid. |
| `validate_todo_shape` | Return missing required TODO fields. |
| `assert_single_in_progress` | Ensure at most one TODO is in progress. |
| `append_event` | Append a TODO event after validation. |
| `next_todo_id` | Generate the next TODO ID. |
| `base_todo` | Build a complete TODO object with default gates. |
| `create_todo` | Create a pending TODO. |
| `create_todos_from_findings` | Convert accepted critical findings into TODOs. |
| `get_todo` | Return one TODO by ID. |
| `list_todos` | Return materialized TODOs, optionally filtered by status. |
| `set_status` | Set TODO status through an append-only event. |
| `start_next_todo` | Start the first pending TODO whose dependencies are completed. |
| `add_validation_evidence` | Append validation evidence to a TODO. |
| `add_review_findings` | Append critical subagent findings to a TODO. |
| `add_review_record` | Record an independent validation/review pass for a TODO. |
| `update_documentation_status` | Update documentation status for a TODO. |
| `completion_blockers` | Return reasons a TODO cannot be completed. |
| `configured_quality_commands` | Return configured test/lint/build/eval commands from RDD state. |
| `has_configured_quality_commands` | Return True when any real quality-gate command is configured. |
| `has_executed_passing_quality_gate` | Return True when TODO evidence includes an executed passing quality gate. |
| `complete_todo_if_ready` | Mark a TODO completed only after all gates are satisfied. |
| `archive_completed_todos` | Move completed TODO event history to `todo_archive/` and leave compact completed stubs in `todos.jsonl`. |
| `update_from_improvement_critique` | Create follow-up TODOs from accepted improvement critique findings. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `validate_skill.py`

Purpose: Validate required files, SKILL.md frontmatter, script compilation, external links, bilingual README, and behavioral smoke test presence.

| Function/class | Intended implementation boundary |
|---|---|
| `check_required_files` | Return missing required file errors. |
| `check_frontmatter` | Validate basic SKILL.md frontmatter. |
| `check_script_compilation` | Compile every Python script. |
| `check_external_links` | Check that external skill links file contains required URLs. |
| `check_bilingual_readme` | Check root README if available through parent layout. |
| `check_optional_tests` | Check that behavioral smoke tests are present in the project package. |
| `validate` | Run all validation checks. |
| `render_report` | Render validation report as Markdown. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## `self_test.py`

Purpose: Run an end-to-end standard-library smoke workflow that proves behavior not covered by static layout validation.

| Function/class | Intended implementation boundary |
|---|---|
| `assert_true` | Raise AssertionError with a clear message. |
| `run_self_test` | Run a full non-destructive workflow smoke test and return evidence. |
| `main` | CLI entrypoint; keep side effects inside a temporary project directory. |

## `workflow_runner.py`

Purpose: Provide high-level orchestration preview and safe state setup that Codex can use to sequence phases.

| Function/class | Intended implementation boundary |
|---|---|
| `run_context_phase` | Inventory project context and build a requirement packet. |
| `run_sync_phase` | Synchronize inventory/cache/context-pack state for fast reuse. |
| `run_overview_phase` | Return the compact context pack for quick Codex reference. |
| `run_semantic_index_phase` | Return bounded semantic locator metadata for quick file lookup. |
| `run_semantic_search_phase` | Return ranked likely files for a semantic query. |
| `run_bootstrap_phase` | Write repo-local fast-context bootstrap guidance. |
| `run_commands_phase` | Return common RDD commands for context/cache/TODO/quality UX. |
| `needs_first_run` | Return True when defaults are missing. |
| `build_first_run_action` | Return the action the main agent should take for first-run setup. |
| `run_preplan_critique_phase` | Write preplan critical-only subagent briefs. |
| `run_todo_generation_phase` | Convert accepted findings into TODOs. |
| `run_execution_phase` | Start the next TODO. |
| `run_validation_phase` | Prepare validation evidence and critical validation briefs. |
| `run_documentation_phase` | Prepare documentation check report. |
| `run_improvement_phase` | Write improvement critical-only subagent briefs. |
| `run_once` | Run a non-mutating orchestration preview plus safe state setup. |
| `main` | CLI entrypoint; keep side effects explicit and bounded to the requested root/path. |

## Codex completion order

1. Run `scripts/validate_skill.py` and `python -m compileall scripts` before changing behavior.
2. Preserve implemented helper contracts in `constants.py`, `requirement_analyzer.py`, `critic_ledger.py`, `doc_sync_check.py`, `subagent_brief_builder.py`, and `workflow_runner.py` when extending behavior.
3. Strengthen completion gates in `todo_manager.py` only after preserving the one-in-progress rule.
4. Improve context and data inference in `context_inventory.py` and `data_profile.py` without reading excessive file contents.
5. Keep `external_skill_registry.py`, `external-skill-links.md`, and `internal-skill-map.md` synchronized.
6. Update README and this contract when function names, state schema, or registration flow changes.
