# Python function contract / Python 함수 계약

This file is generated from the current `scripts/*.py` files. It lists each public function/class and the implemented helper contract. Codex should preserve these public contracts when extending behavior.

이 파일은 현재 `scripts/*.py`에서 추출한 함수/클래스 목록입니다. Codex는 공개 함수명을 유지하고 구현 세부사항을 확장해야 합니다.

## Completion order / 구현 우선순위

1. `rdd_state.py` — first-run profile/defaults persistence
2. `context_inventory.py` and `requirement_analyzer.py` — source/docs/data requirement understanding
3. `subagent_brief_builder.py` and `critic_ledger.py` — critical-only debate and decision capture
4. `todo_manager.py` — TODO lifecycle and update loop
5. `quality_gate.py` and `data_profile.py` — TDD/data validation evidence
6. `doc_sync_check.py` — documentation gate
7. `external_skill_registry.py`, `skill_registration.py`, `validate_skill.py` — external links and Codex registration
8. `workflow_runner.py` — optional orchestration preview; main Codex agent still owns judgment
9. `self_test.py` and `tests/test_smoke_workflow.py` — behavioral smoke validation

## Script index / 스크립트 색인

| File | Main symbols | Role |
|---|---|---|
| `constants.py` | `utc_now`, `utc_stamp`, `project_state_dir`, `safe_slug`, `ensure_directory`, `markdown_title_from_filename`, `csv_line` | Shared constants and tiny helpers for review-driven-development. |
| `context_inventory.py` | `now_iso`, `should_skip`, `iter_files`, `classify_file`, `collect_classified_files`, `count_languages`, `group_paths`, `read_text_snippet` … | Context inventory, cache, and context-pack helper for review-driven-development. |
| `critic_ledger.py` | `findings_path`, `normalize_severity`, `normalize_decision`, `create_finding`, `append_finding`, `read_findings`, `decide_finding`, `reconstruct_findings` … | Critical finding and decision ledger helper. |
| `data_profile.py` | `now_iso`, `detect_dialect`, `iter_delimited_rows`, `iter_jsonl_rows`, `profile_rows`, `profile_data_file`, `discover_data_files`, `build_data_profile_report` … | Data profiling helper for the `review-driven-development` data/CSV critic. |
| `doc_sync_check.py` | `now_iso`, `filename_timestamp`, `path_exists`, `discover_docs`, `infer_targets_from_files`, `load_todo`, `infer_targets_for_todo`, `build_doc_sync_report` … | Documentation synchronization checker helper. |
| `external_skill_registry.py` | `ExternalSkill`, `all_skills`, `skills_for_phase`, `required_skills`, `find_skill`, `install_hints`, `render_markdown`, `as_json` … | External skill registry for review-driven-development. |
| `quality_gate.py` | `now_iso`, `filename_timestamp`, `load_json`, `normalize_commands`, `load_commands`, `select_commands`, `run_command`, `evaluate_results` … | Quality gate evidence helper for review-driven-development. |
| `rdd_state.py` | `now_iso`, `filename_timestamp`, `resolve_root`, `state_path`, `initial_text_for`, `ensure_state`, `read_json`, `write_json` … | Project-local state helper for the review-driven-development skill. |
| `requirement_analyzer.py` | `Option`, `RequirementPacket`, `summarize_prompt`, `extract_constraints`, `infer_language_options`, `build_method_options`, `build_existing_code_options`, `build_validation_options` … | Requirement analysis helper. |
| `skill_registration.py` | `candidate_install_dirs`, `read_frontmatter`, `validate_skill_folder`, `install_skill`, `main` | Skill registration helper for review-driven-development. |
| `skill_registration_helper.py` | `LayoutReport`, `validate_skill_layout`, `suggest_targets`, `copy_skill`, `registration_commands`, `main` | Skill registration helper for review-driven-development. |
| `subagent_brief_builder.py` | `RoleSpec`, `now_stamp`, `get_role_spec`, `load_inventory`, `role_list_for_phase`, `build_brief`, `write_briefs`, `parse_findings_placeholder` … | Subagent brief builder for review-driven-development. |
| `todo_manager.py` | `now_iso`, `todos_path`, `read_events`, `deep_merge`, `current_state`, `validate_status`, `validate_todo_shape`, `assert_single_in_progress` … | TODO ledger helper for the review-driven-development skill. |
| `validate_skill.py` | `check_required_files`, `check_frontmatter`, `check_script_compilation`, `check_external_links`, `check_bilingual_readme`, `check_optional_tests`, `validate`, `render_report`, `main` | Validate the review-driven-development skill package. |
| `workflow_runner.py` | `run_context_phase`, `run_sync_phase`, `run_overview_phase`, `run_semantic_index_phase`, `run_bootstrap_phase`, `run_commands_phase`, `needs_first_run`, `build_first_run_action` … | High-level workflow orchestration and command UX preview. |
| `self_test.py` | `assert_true`, `run_self_test`, `main` | End-to-end standard-library smoke workflow validation. |

## `constants.py`

Shared constants and tiny helpers for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `utc_now` | function | Return an ISO-8601 UTC timestamp without microseconds. |
| `utc_stamp` | function | Return a compact UTC timestamp for filenames. |
| `project_state_dir` | function | Return the project-local RDD state directory path. |
| `safe_slug` | function | Create a filesystem-safe lowercase slug. |
| `ensure_directory` | function | Create a directory if missing and return it as a resolved Path. |
| `markdown_title_from_filename` | function | Return a human-readable title for a markdown ledger filename. |
| `csv_line` | function | Return a simple comma-separated line for tiny human diagnostics. |

## `context_inventory.py`

Context inventory, cache, and context-pack helper for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `now_iso` | function | Return a stable UTC timestamp. |
| `should_skip` | function | Return True if any path component should be skipped. |
| `iter_files` | function | Yield files under root with a hard scan cap. |
| `classify_file` | function | Classify one file for planning and critic selection. |
| `collect_classified_files` | function | Return classified file metadata. |
| `count_languages` | function | Count detected source languages. |
| `group_paths` | function | Group paths into source/doc/data/test/build categories. |
| `read_text_snippet` | function | Read a small UTF-8 snippet, returning empty string for binary/failed reads. |
| `tokenize_for_index` | function | Return stable high-signal terms for a semantic locator index. |
| `extract_symbols` | function | Extract shallow function/class/interface symbols from one text file. |
| `split_identifier_terms` | function | Expand snake/camel/path identifiers into searchable terms. |
| `build_search_text` | function | Build bounded text used by semantic ranking backends. |
| `sklearn_available` | function | Return True when scikit-learn semantic ranking can be used. |
| `sentence_transformers_available` | function | Return True when dense embedding ranking can be used. |
| `encode_embedding_texts` | function | Encode texts with SentenceTransformers, returning JSON-serializable vectors. |
| `dot_score` | function | Return cosine score for normalized vectors, or dot-product fallback. |
| `collect_doc_snippets` | function | Collect snippets from key Markdown/spec files. |
| `prioritize_paths` | function | Return paths ordered for compact Codex context consumption. |
| `unique_ordered` | function | Return unique paths while preserving the incoming order. |
| `build_file_fingerprint` | function | Build a cheap project fingerprint without reading file contents. |
| `build_semantic_index` | function | Build a bounded lexical/symbol index for quick file location. |
| `summarize_semantic_index` | function | Return compact semantic index metadata for context packs and cache. |
| `search_semantic_index` | function | Rank semantic index files for a query using TF-IDF when available. |
| `infer_frameworks` | function | Infer likely frameworks from manifests and build files. |
| `choose_recommended_critics` | function | Choose critic roles based on the inventory. |
| `build_inventory` | function | Build the full project context inventory. |
| `build_context_pack` | function | Build a compact Markdown pack optimized for quick Codex reference. |
| `summarize_inventory` | function | Return a human-readable summary for prompts and briefs. |
| `save_inventory` | function | Save context inventory under project state. |
| `save_context_pack` | function | Save a compact Markdown context pack for fast Codex loading. |
| `save_context_cache` | function | Save cache metadata used to reuse inventory and context packs safely. |
| `save_semantic_index` | function | Save the semantic locator index under project state. |
| `load_inventory` | function | Load saved context inventory if it exists. |
| `load_context_pack` | function | Load the compact context pack if present. |
| `load_context_cache` | function | Load context cache metadata if present and parseable. |
| `load_semantic_index` | function | Load the semantic locator index if present and parseable. |
| `detect_context_script` | function | Return the best repo-local context inventory command path. |
| `build_bootstrap_block` | function | Build an AGENTS.md block that injects fast context instructions. |
| `write_bootstrap` | function | Insert or replace the RDD fast-context bootstrap block in a repo file. |
| `sync_context` | function | Reuse valid context cache or rebuild inventory and compact context pack. |
| `main` | function | CLI entrypoint for context inventory generation. |

## `critic_ledger.py`

Critical finding and decision ledger helper.

| Symbol | Type | Contract role |
|---|---|---|
| `findings_path` | function | Return and initialize the findings JSONL path. |
| `normalize_severity` | function | Normalize severity to allowed values. |
| `normalize_decision` | function | Normalize main-agent decision to allowed values. |
| `create_finding` | function | Create a normalized finding record. |
| `append_finding` | function | Append a finding to the JSONL ledger. |
| `read_findings` | function | Read finding events from JSONL. |
| `decide_finding` | function | Append a decision event for a finding. |
| `reconstruct_findings` | function | Reconstruct current finding state from append-only events. |
| `open_findings` | function | Return findings without a final decision. |
| `accepted_findings` | function | Return findings accepted by the main agent. |
| `findings_to_todo_seeds` | function | Convert accepted findings into TODO seed dictionaries. |
| `append_decision_markdown` | function | Append a human-readable decision entry. |
| `main` | function | CLI entrypoint for basic finding ledger operations. |

## `data_profile.py`

Data profiling helper for the `review-driven-development` data/CSV critic.

| Symbol | Type | Contract role |
|---|---|---|
| `now_iso` | function | Return a stable UTC timestamp for data reports. |
| `detect_dialect` | function | Detect basic delimiter/format hints for a text data file. |
| `iter_delimited_rows` | function | Yield rows from a CSV/TSV-like file up to `max_rows`. |
| `iter_jsonl_rows` | function | Yield JSON objects from a JSONL/NDJSON file up to `max_rows`. |
| `profile_rows` | function | Profile rows for schema, missing values, simple uniqueness, and examples. |
| `profile_data_file` | function | Profile one supported data file. |
| `discover_data_files` | function | Discover lightweight text data files under `root`. |
| `build_data_profile_report` | function | Build a data profile report for one or more files. |
| `save_report` | function | Persist a data profile report under project state. |
| `main` | function | CLI entrypoint for data profiling. |

## `doc_sync_check.py`

Documentation synchronization checker helper.

| Symbol | Type | Contract role |
|---|---|---|
| `now_iso` | function | Return a stable UTC timestamp. |
| `filename_timestamp` | function | Return timestamp for report filenames. |
| `path_exists` | function | Check whether a documentation target exists. |
| `discover_docs` | function | Return found and missing documentation targets. |
| `infer_targets_from_files` | function | Infer documentation targets from changed files. |
| `load_todo` | function | Load a materialized TODO from todos.jsonl if available. |
| `infer_targets_for_todo` | function | Infer documentation targets from TODO metadata and changed files. |
| `build_doc_sync_report` | function | Build a documentation synchronization report. |
| `save_report` | function | Save a documentation sync report under project state. |
| `main` | function | CLI entrypoint for documentation synchronization checks. |

## `external_skill_registry.py`

External skill registry for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `ExternalSkill` | class | A skill dependency or recommended external workflow. |
| `all_skills` | function | Return every external skill entry. |
| `skills_for_phase` | function | Return skills associated with a phase. |
| `required_skills` | function | Return skills marked required by the RDD workflow. |
| `find_skill` | function | Find a skill entry by name, case-insensitive. |
| `install_hints` | function | Return install commands/hints for selected skill names. |
| `render_markdown` | function | Render skill entries as Markdown with explicit links and install hints. |
| `as_json` | function | Render skill entries as JSON. |
| `write_registry` | function | Write registry to a file as JSON or Markdown. |
| `main` | function | CLI entrypoint for external skill registry. |

## `quality_gate.py`

Quality gate evidence helper for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `now_iso` | function | Return a stable UTC timestamp. |
| `filename_timestamp` | function | Return timestamp for report filenames. |
| `load_json` | function | Load JSON if available, otherwise return default. |
| `normalize_commands` | function | Normalize command mapping into lists for test/lint/build/eval. |
| `load_commands` | function | Load quality-gate commands from commands.json or defaults.json. |
| `select_commands` | function | Select commands in stable kind order. |
| `run_command` | function | Execute a shell command and return bounded evidence. |
| `evaluate_results` | function | Summarize pass/fail status for executed quality gates. |
| `build_report` | function | Build the validation report object. |
| `save_report` | function | Save validation report under project state. |
| `record_report_as_todo_evidence` | function | Append a saved quality-gate report path to the TODO evidence ledger. |
| `run_quality_gate` | function | Select, optionally execute, and save quality-gate evidence. |
| `main` | function | CLI entrypoint for quality-gate command selection and execution. |

## `rdd_state.py`

Project-local state helper for the review-driven-development skill.

| Symbol | Type | Contract role |
|---|---|---|
| `now_iso` | function | Return a stable UTC timestamp. |
| `filename_timestamp` | function | Return a filename-safe UTC timestamp. |
| `resolve_root` | function | Resolve and validate the target project root. |
| `state_path` | function | Return the persistent state directory path for a project root. |
| `initial_text_for` | function | Return default content for a new state file. |
| `ensure_state` | function | Create the state directory and baseline ledger files without overwriting. |
| `read_json` | function | Read a JSON file; return `default` if absent. |
| `write_json` | function | Write deterministic UTF-8 JSON with explicit overwrite control. |
| `default_defaults` | function | Return conservative first-run defaults for the skill. |
| `normalize_language` | function | Normalize language labels to `ko` or `en`. |
| `merge_preserving_safety` | function | Merge defaults while preserving destructive-change safety settings. |
| `parse_command_hints` | function | Extract common test/lint/build/eval commands from free text. |
| `parse_first_run_answers` | function | Parse first-run answers into durable defaults. |
| `load_defaults` | function | Load project defaults if initialized. |
| `write_defaults` | function | Persist parsed defaults. |
| `write_profile` | function | Persist the exact first-run answer as Markdown. |
| `initialize_project_state` | function | Initialize profile and defaults together after the first-run questionnaire. |
| `update_defaults` | function | Update defaults using conservative merge semantics. |
| `append_markdown` | function | Append a timestamped Markdown section to a state ledger. |
| `append_decision` | function | Append an accepted/rejected/deferred critique decision. |
| `append_review_summary` | function | Append a critical subagent review summary. |
| `append_implementation_log` | function | Append implementation evidence for a completed or blocked TODO. |
| `update_commands` | function | Write project-specific quality-gate commands. |
| `load_context_inventory` | function | Load saved context inventory if present. |
| `status` | function | Return a compact state summary. |
| `main` | function | Command-line entrypoint for state operations. |

## `requirement_analyzer.py`

Requirement analysis helper.

| Symbol | Type | Contract role |
|---|---|---|
| `Option` | class | A candidate option with tradeoffs. |
| `RequirementPacket` | class | Structured packet consumed by planning and critic phases. |
| `summarize_prompt` | function | Create a compact prompt summary. |
| `extract_constraints` | function | Extract hard constraints from prompt and Markdown text. |
| `infer_language_options` | function | Infer plausible implementation languages from inventory. |
| `build_method_options` | function | Return implementation method options with pros and cons. |
| `build_existing_code_options` | function | Return reuse/review/refactor/rewrite options. |
| `build_validation_options` | function | Return validation strategy options. |
| `build_documentation_options` | function | Return documentation strategy options. |
| `build_first_run_questions` | function | Build first-run questions based on context. |
| `create_requirement_packet` | function | Create a structured requirement packet for critic/planning phases. |
| `render_packet_markdown` | function | Render a first-response packet with pros/cons. |
| `packet_to_dict` | function | Convert packet dataclasses into plain dictionaries. |
| `main` | function | CLI entrypoint for drafting a requirement packet. |

## `skill_registration.py`

Skill registration helper for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `candidate_install_dirs` | function | Return common Codex-discoverable install locations. |
| `read_frontmatter` | function | Read minimal YAML-like frontmatter from SKILL.md. |
| `validate_skill_folder` | function | Return validation errors for a skill folder. |
| `install_skill` | function | Install a skill folder by copying or symlinking it. |
| `main` | function | CLI entrypoint for local skill validation and installation. |

## `skill_registration_helper.py`

Skill registration helper for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `LayoutReport` | class | Skill layout validation result. |
| `validate_skill_layout` | function | Check whether `skill_dir` looks like a Codex skill. |
| `suggest_targets` | function | Return Codex-supported skill save targets. |
| `copy_skill` | function | Copy the skill directory to a Codex skill target. |
| `registration_commands` | function | Return shell commands for manual registration. |
| `main` | function | CLI entrypoint for registration assistance. |

## `subagent_brief_builder.py`

Subagent brief builder for review-driven-development.

| Symbol | Type | Contract role |
|---|---|---|
| `RoleSpec` | class | Definition of one critical-only subagent role. |
| `now_stamp` | function | Return timestamp for brief directory names. |
| `get_role_spec` | function | Return a role spec, with a generic fallback. |
| `load_inventory` | function | Load saved context inventory if present. |
| `role_list_for_phase` | function | Return critic roles for a phase using inventory hints. |
| `build_brief` | function | Build a Markdown prompt for one critical-only subagent. |
| `write_briefs` | function | Write critical-only briefs for one phase. |
| `parse_findings_placeholder` | function | Placeholder parser for subagent findings. |
| `build_decision_table` | function | Create a decision table template for the main agent. |
| `main` | function | CLI entrypoint for writing critical-only subagent briefs. |

## `todo_manager.py`

TODO ledger helper for the review-driven-development skill.

| Symbol | Type | Contract role |
|---|---|---|
| `now_iso` | function | Return a stable UTC timestamp. |
| `todos_path` | function | Return TODO ledger path, creating the parent directory. |
| `read_events` | function | Read append-only TODO events. |
| `deep_merge` | function | Merge nested dictionaries while replacing non-dict values. |
| `current_state` | function | Materialize current TODO state from ledger events. |
| `validate_status` | function | Raise if status is invalid. |
| `validate_todo_shape` | function | Return missing required TODO fields. |
| `assert_single_in_progress` | function | Ensure at most one TODO is in progress. |
| `append_event` | function | Append a TODO event after validation. |
| `next_todo_id` | function | Generate the next TODO ID. |
| `base_todo` | function | Build a complete TODO object with default gates. |
| `create_todo` | function | Create a pending TODO. |
| `create_todos_from_findings` | function | Convert accepted critical findings into TODOs. |
| `get_todo` | function | Return one TODO by ID. |
| `list_todos` | function | Return materialized TODOs, optionally filtered by status. |
| `set_status` | function | Set TODO status through an append-only event. |
| `start_next_todo` | function | Start the first pending TODO whose dependencies are completed. |
| `add_validation_evidence` | function | Append validation evidence to a TODO. |
| `add_review_findings` | function | Append critical subagent findings to a TODO. |
| `add_review_record` | function | Record an independent validation/review pass for a TODO. |
| `update_documentation_status` | function | Update documentation status for a TODO. |
| `completion_blockers` | function | Return reasons a TODO cannot be completed. |
| `configured_quality_commands` | function | Return configured test/lint/build/eval commands from RDD state. |
| `has_configured_quality_commands` | function | Return True when any real quality-gate command is configured. |
| `has_executed_passing_quality_gate` | function | Return True when TODO evidence includes an executed passing quality gate. |
| `complete_todo_if_ready` | function | Mark a TODO completed only after all gates are satisfied. |
| `update_from_improvement_critique` | function | Create follow-up TODOs from accepted improvement critique findings. |
| `main` | function | CLI entrypoint for TODO ledger operations. |

## `validate_skill.py`

Validate the review-driven-development skill package.

| Symbol | Type | Contract role |
|---|---|---|
| `check_required_files` | function | Return missing required file errors. |
| `check_frontmatter` | function | Validate basic SKILL.md frontmatter. |
| `check_script_compilation` | function | Compile every Python script. |
| `check_external_links` | function | Check that external skill links file contains required URLs. |
| `check_bilingual_readme` | function | Check root README if available through parent layout. |
| `check_optional_tests` | function | Check that behavioral smoke tests are present in the project package. |
| `validate` | function | Run all validation checks. |
| `render_report` | function | Render validation report as Markdown. |
| `main` | function | CLI entrypoint. |

## `workflow_runner.py`

High-level workflow orchestration preview.

| Symbol | Type | Contract role |
|---|---|---|
| `run_context_phase` | function | Inventory project context and build a requirement packet. |
| `run_sync_phase` | function | Synchronize inventory/cache/context-pack state for fast reuse. |
| `run_overview_phase` | function | Return the compact context pack for quick Codex reference. |
| `run_semantic_index_phase` | function | Return the bounded semantic locator index for quick file lookup. |
| `run_semantic_search_phase` | function | Return ranked likely files for a semantic query. |
| `run_bootstrap_phase` | function | Write repo-local fast-context bootstrap guidance. |
| `run_commands_phase` | function | Return common RDD commands for context/cache/TODO/quality UX. |
| `needs_first_run` | function | Return True when defaults are missing. |
| `build_first_run_action` | function | Return the action the main agent should take for first-run setup. |
| `run_preplan_critique_phase` | function | Write preplan critical-only subagent briefs. |
| `run_todo_generation_phase` | function | Convert accepted findings into TODOs. |
| `run_execution_phase` | function | Start the next TODO. |
| `run_validation_phase` | function | Prepare validation evidence and critical validation briefs. |
| `run_documentation_phase` | function | Prepare documentation check report. |
| `run_improvement_phase` | function | Write improvement critical-only subagent briefs. |
| `run_once` | function | Run a non-mutating orchestration preview plus safe state setup. |
| `main` | function | CLI entrypoint for workflow preview. |

## `self_test.py`

End-to-end standard-library smoke workflow validation.

| Symbol | Type | Contract role |
|---|---|---|
| `assert_true` | function | Raise AssertionError with a clear message. |
| `run_self_test` | function | Run a full non-destructive workflow smoke test and return evidence. |
| `main` | function | CLI entrypoint. |

## Required validation commands / 필수 검증 명령

```bash
python -m compileall skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/skill_registration.py --validate-only
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase overview
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

## Codex completion rules / Codex 구현 규칙

1. Do not break function signatures without updating this file and `scripts/README.md`.
2. Keep state files backward-compatible.
3. Do not auto-accept subagent findings; record a main-agent decision.
4. Do not mark a TODO complete without acceptance criteria, validation evidence, review handling, and documentation status.
5. Keep destructive operations opt-in and user-confirmed.
