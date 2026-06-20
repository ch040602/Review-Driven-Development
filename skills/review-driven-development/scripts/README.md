# Scripts for `review-driven-development`

Each file is dependency-light and implements a bounded helper contract for the main `review-driven-development` workflow.

| File | Main symbols | Role |
|---|---|---|
| `constants.py` | `utc_now`, `utc_stamp`, `project_state_dir`, `safe_slug`, `ensure_directory`, `markdown_title_from_filename`, `csv_line` | Shared constants and tiny helpers for review-driven-development. |
| `context_inventory.py` | `now_iso`, `should_skip`, `iter_files`, `classify_file`, `collect_classified_files`, `count_languages`, `group_paths`, `read_text_snippet` … | Context inventory, cache, compact pack, semantic index, and bootstrap for review-driven-development. |
| `critic_ledger.py` | `findings_path`, `normalize_severity`, `normalize_decision`, `create_finding`, `append_finding`, `read_findings`, `decide_finding`, `reconstruct_findings` … | Critical finding and decision ledger. |
| `data_profile.py` | `now_iso`, `detect_dialect`, `iter_delimited_rows`, `iter_jsonl_rows`, `profile_rows`, `profile_data_file`, `discover_data_files`, `build_data_profile_report` … | Data profiling for the `review-driven-development` data/CSV critic. |
| `doc_sync_check.py` | `now_iso`, `filename_timestamp`, `path_exists`, `discover_docs`, `infer_targets_from_files`, `load_todo`, `infer_targets_for_todo`, `build_doc_sync_report` … | Documentation synchronization checker. |
| `external_skill_registry.py` | `ExternalSkill`, `all_skills`, `skills_for_phase`, `required_skills`, `find_skill`, `install_hints`, `render_markdown`, `as_json` … | External skill registry for review-driven-development. |
| `quality_gate.py` | `now_iso`, `filename_timestamp`, `load_json`, `normalize_commands`, `load_commands`, `select_commands`, `run_command`, `evaluate_results` … | Quality gate evidence helper for review-driven-development. |
| `rdd_state.py` | `now_iso`, `filename_timestamp`, `resolve_root`, `state_path`, `initial_text_for`, `ensure_state`, `read_json`, `write_json` … | Project-local state helper for the review-driven-development skill. |
| `requirement_analyzer.py` | `Option`, `RequirementPacket`, `summarize_prompt`, `extract_constraints`, `infer_language_options`, `build_method_options`, `build_existing_code_options`, `build_validation_options` … | Requirement analysis helper. |
| `skill_registration.py` | `candidate_install_dirs`, `read_frontmatter`, `validate_skill_folder`, `install_skill`, `main` | Skill registration helper for review-driven-development. |
| `skill_registration_helper.py` | `LayoutReport`, `validate_skill_layout`, `suggest_targets`, `copy_skill`, `registration_commands`, `main` | Skill registration helper for review-driven-development. |
| `subagent_brief_builder.py` | `RoleSpec`, `now_stamp`, `get_role_spec`, `load_inventory`, `role_list_for_phase`, `build_brief`, `write_briefs`, `parse_findings_placeholder` … | Subagent brief builder for review-driven-development. |
| `todo_manager.py` | `now_iso`, `todos_path`, `read_events`, `deep_merge`, `current_state`, `validate_status`, `validate_todo_shape`, `assert_single_in_progress` … | TODO ledger helper for the review-driven-development skill. |
| `validate_skill.py` | `check_required_files`, `check_frontmatter`, `check_script_compilation`, `check_external_links`, `check_bilingual_readme`, `validate`, `render_report`, `main` | Validate the review-driven-development skill draft. |
| `workflow_runner.py` | `run_context_phase`, `run_sync_phase`, `run_overview_phase`, `run_semantic_index_phase`, `run_bootstrap_phase`, `run_commands_phase` … | High-level workflow preview, safe state setup, and command UX. |

## Fast context/cache UX

```bash
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --overview
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "quality gate completion"
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --role-map
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase overview
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-index
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-search --query "quality gate completion"
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase role-map
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase validation --todo-id RDD-T-00000001 --agent-budget spark-first
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase commands
```

Install `python -m pip install -e ".[semantic]"` for default TF-IDF ranking through `scikit-learn`; lexical fallback remains available without it. Install `python -m pip install -e ".[embeddings]"` and pass `--embeddings` only when dense `sentence-transformers` ranking is worth the model-load cost. Default `self_test.py` avoids embedding model loading; run `python skills/review-driven-development/scripts/self_test.py --embeddings` for explicit embedding validation.

## Validation

```bash
python -m compileall scripts
python scripts/validate_skill.py --skill-dir .
```

## Behavioral smoke validation

Run:

```bash
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

`self_test.py` verifies first-run detection, context cache/pack generation, semantic index generation, embedding/TF-IDF/fallback semantic search behavior, AGENTS bootstrap injection, command UX, accepted critic finding to TODO conversion, one active TODO, deferred validation/improvement until after implementation, quality-gate evidence, independent review record, documentation status, and TODO completion gates.
