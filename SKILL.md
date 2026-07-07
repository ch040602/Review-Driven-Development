---
name: review-driven-development
description: RDD workflow for TODO planning, validation, review, docs, compact state, and completion loops.
---

# review-driven-development

## Mission

Run one integrated workflow:

```text
requirements -> first-run defaults -> compact source/file analysis -> rule-gated critical subagents -> main-agent decisions -> TODO plan -> one TODO execution -> TDD validation -> independent critical review -> documentation -> gated improvement critique -> TODO update -> repeat -> optional ChatGPT Pro TODO replenishment only when active TODOs are terminal
```

Optimize for completeness, correctness, maintainability, traceability, research usefulness, and fast context reuse. Prefer compact evidence packets and rule-based narrowing before spending LLM/subagent tokens. Before TODO generation, prefer the minimal solution ladder: prove the feature is necessary, reuse existing code, prefer stdlib/native/installed dependencies, try a one-line/local change, then implement minimal code only if still justified.

## Token-Budget Defaults

Use the smallest mode that can safely answer the current TODO.

- `fast`: small/local edits, docs-only changes, or already-known target files. Inventory is capped aggressively and snippets are omitted.
- `standard`: default mode. Inventory records ranked source/docs/tests/build/data lists, omits snippets by default, and generates only high-signal critic briefs.
- `deep`: opt-in for broad migrations, security-sensitive work, data-heavy work, unfamiliar frameworks, or when validation/review finds missing context.

Dense `sentence-transformers` ranking is opt-in with `--embeddings`; default semantic search uses `scikit-learn` TF-IDF when installed, then lexical overlap.

Additional operating goals:

- Reduce first-response latency by reusing `context-cache.json` and avoiding model loads unless requested.
- Keep generated critic briefs small enough to inspect quickly while preserving blocker/high-risk review coverage.
- Prefer targeted file ranking over broad source-tree reads.
- Read the `Role map` in `context-pack.md` before any broad exploration; use its query hints to choose one responsibility boundary.
- Preserve an explicit `deep` path for high-risk work instead of silently weakening review quality.
- Keep `minimalism_level` separate from `fast`/`standard`/`deep`; default to `full` and put long policy in `references/minimal-solution-policy.md`.
- Keep skill discovery cheap: the frontmatter `description` must stay concise. Put workflow detail in this body and references, not in the description field that every Codex session preloads.
- Keep active TODO state cheap: after each completed TODO, archive full completed history to `todo_archive/` and keep only dependency-safe stubs in `todos.jsonl`.

## Execution modes

Default mode is `one-todo`: execute exactly one accepted/actionable TODO, validate it, document it, and report the next TODO.

`until-complete` mode is activated when the user explicitly says `완료까지`, `until complete`, `complete all actionable TODOs`, `모든 진행 가능한 TODO 완료`, or equivalent wording. In this mode:

- Continue one TODO at a time until no actionable TODO remains in the current accepted backlog.
- Do not stop after a single TODO, optional critique, optional Pro feedback, or non-blocking uncertainty.
- Do not call ChatGPT Pro during the per-TODO execution loop. Even when Pro feedback is explicitly requested, finish, block, or defer every active TODO first, then use Pro only to replenish the TODO backlog.
- Use reasonable defaults instead of asking for optional input; ask only when continuing would be unsafe, destructive, or would require secrets/credentials the user has not provided.
- For each actionable TODO: set exactly one item `in_progress`, implement, validate, document evidence, run justified critique, then mark it `completed`.
- For each not-currently-executable TODO: do not keep retrying indefinitely. Move it to `todo_remain.jsonl` with status `deferred` or `blocked`, concrete reason, required external dependency, last evidence, and the command/manual action needed to resume.
- Treat external services, paid accounts, missing SDKs/editors/devices, manual QA, legal/store review, credentials, unavailable local files, unsafe/disallowed actions, or user-only approvals as valid reasons to move work to `todo_remain`.
- The run may finish only after all TODOs are either completed or recorded in `todo_remain.jsonl` as not currently executable.

`bounded-pro-feedback-cycle` mode is activated only when the user explicitly asks for a numeric Pro feedback loop such as `5회 반복`, `5회 재귀`, `repeat Pro feedback 5 times`, or equivalent wording. In this mode:

- Cap live provider rounds at the requested count, with an absolute maximum of 5.
- For each cycle: complete or defer every active locally actionable TODO first, sync structure/completeness context, commit and push any repo changes, run exactly one Pro review round to replenish TODOs, import accepted findings, execute any newly imported locally actionable TODOs to completion, then validate and commit/push evidence before moving to the next cycle.
- Do not call Pro while any TODO is `in_progress`.
- Move external/manual findings to `todo_remain.jsonl` immediately instead of retrying them in the same cycle.
- If a cycle imports no locally actionable TODOs, still record provider artifacts, validation evidence, and push before continuing to the next requested cycle.
- This numeric bounded-cycle rule is the explicit exception to the
  `agbrowse-chatgpt-pro-review` single-replenishment stop rule. Do not treat
  that exception as permission for unbounded repeated provider calls: cap at the
  requested count, absolute maximum 5, and use the same pinned ChatGPT
  conversation while asking only for non-duplicate locally actionable TODOs.
- Stop early only for a hard blocker that cannot be deferred, provider unavailability after a documented retry with smaller context, failed validation that cannot be fixed locally, or a user interruption.

## Non-negotiable rules

1. Keep this as one user-facing skill: `review-driven-development`.
2. Use other skills only internally and record where they influenced the decision.
3. On first use in a project, ask `references/first-run-questionnaire.md` questions and save exact answers.
4. Persist defaults under `.codex/review-driven-development/` and use them silently on later runs unless the user overrides them.
5. Analyze prompt text, attached files, Markdown docs, `AGENTS.md`, source files, tests, build files, and data files before planning, but start from compact inventory summaries and targeted reads.
6. If existing code exists, ask whether to reuse, review, refactor, replace, isolate, or decide per TODO. If defaults exist, follow the saved policy.
7. Use subagents only when a rule-based signal or unresolved uncertainty justifies parallel critical review. Default to `standard` critic depth; use `minimal` for low-risk local work and `deep` only for concrete broad/high-risk work.
8. Debate, validation, review, and improvement subagents are **critical-only**: they identify risks and missing evidence; they do not decide or patch.
9. The main agent alone classifies feedback as `accept`, `reject`, `defer`, or `needs_user_input`.
10. Only accepted feedback becomes TODOs.
11. Keep exactly one TODO as `in_progress`.
12. Use `test-driven-development` for behavior changes and validation. When practical, write or update a failing test before implementation.
13. Use `systematic-debugging` for failed checks before broad changes.
14. Do not mark a TODO completed until evidence, validation notes, review notes, and documentation status are recorded.
15. After each TODO, run improvement critique only at the depth justified by risk: `minimal` for straightforward validated changes, `standard` by default, `deep` for data/security/architecture/performance-sensitive work.
16. Run the minimal-solution ladder before creating TODOs that add files, dependencies, config, abstractions, scanners, parsers, or workflows; record the packet when the gate changes the plan.
17. Invoke the `agbrowse-chatgpt-pro-review` companion only when the user explicitly requests ChatGPT Pro/Pro/external AI feedback, passes `--pro-review`, or requests recursive Pro review, and only after every active TODO is `completed`, `blocked`, or `deferred`. Never use Pro as an automatic per-TODO, post-validation, or improvement-loop critic. Store generated Markdown/YAML context packets, raw responses, extracted TODO candidates, and created TODO IDs under `.codex/review-driven-development/pro-review/`.
18. ChatGPT Pro review is a TODO replenishment step, not a critic cadence. Run at most one live provider round after the active RDD TODO backlog is terminal. Exception: when the user explicitly requests a bounded numeric Pro feedback cycle, run up to that count with an absolute maximum of 5, and execute the full local TODO completion/validation/push loop between provider rounds. Do not set `--pro-review-count` above 1 for any single `workflow_runner.py --phase pro-review` invocation; implement multi-cycle feedback as repeated one-round invocations separated by local TODO execution, validation, documentation, commit, and push.
19. Every context sync must update `.codex/review-driven-development/project-structure-completeness.md` and `.codex/review-driven-development/project-structure-completeness.json` with the current folder structure, inferred file roles, and heuristic completeness status. Read the Markdown file before requesting Pro feedback.
20. In `until-complete` mode, complete every locally actionable TODO before stopping. If a TODO cannot be executed now, record it in `todo_remain.jsonl` instead of leaving it as an unclassified pending item.
21. For recursive ChatGPT Pro feedback on game-shipping projects, the Pro context must explicitly state the final product goal, current runtime target, and executable boundary. For `FLUX DERBY`, always state: final objective is a Steam-releaseable Unity 2D pixel-art game, not a console/WinForms app; local TODOs must be executable without Unity Editor, Steamworks, external downloads, credentials, rendered capture, or manual QA unless those dependencies are already available.
22. Archive completed TODO event history by default. Prefer `todo_manager.py complete <id>` so completion immediately writes full history to `todo_archive/` and leaves only compact completed stubs in `todos.jsonl`; use `--keep-in-ledger` only for debugging.

## Rule-Based Subagent Triggers

Default critic selection is generated by `scripts/subagent_brief_builder.py` from `context-inventory.json`.

- Always consider requirements, TDD/validation, and reuse/greenfield-scope critics.
- Add `data-csv-critic` only when data files are detected or the user task is data/evaluation-heavy.
- Add `security-risk-critic` only when filenames/task context show auth, secrets, tokens, permissions, privacy, destructive operations, or deployment risk.
- Add `source-driven-framework-critic` only when framework/build manifests are detected or a framework/API claim must be grounded.
- Add documentation critics only when docs are present and likely to affect behavior, installation, API, or user-facing guidance.
- Cap generated briefs unless the user explicitly requests deep review or the main agent records an escalation reason.

## Subagent Intelligence Allocation

Generated briefs include an agent allocation hint. Treat tier names as routing labels for the orchestrator, not as a replacement for the critical-only contract.

- `spark-first` is the default. Use `codex-spark` freely for frequent structured checks: requirements, tests, validation evidence, docs, maintainability, and quality checklists.
- Escalate to `codex-standard` for framework/source grounding, runtime tradeoffs, reuse/refactor coupling, performance/accuracy review, or any role that needs non-mechanical cross-file reasoning.
- Escalate to `codex-deep` for security, data correctness, architecture blockers, broad migrations, or when `critic-depth=deep` is explicitly selected.
- If a `codex-spark` pass reports blocker/high severity, missing evidence, or cross-module uncertainty, rerun only that role at the next tier instead of broadening every subagent.
- Preserve the main-agent decision boundary: subagents identify risks; the main agent accepts, rejects, defers, or asks the user.
- Custom agent configs under `.codex/agents/` and spawn plans are scaffolds for explicit subagent use; do not claim Spark or any subagent executed unless it actually ran.

## Required state files

Create or update this directory in the target project:

```text
.codex/review-driven-development/
```

Minimum files:

```text
profile.md              # exact first-run answers and project assumptions
defaults.json           # parsed defaults used when no new instruction is provided
todos.jsonl             # active TODO lifecycle ledger plus compact completed stubs
critic-findings.jsonl   # append-only critical subagent findings
decision-log.md         # accepted/rejected/deferred findings
review-ledger.md        # review and validation summaries
implementation-log.md   # completed work, evidence, docs status
commands.json           # test/lint/build/eval commands when known
context-inventory.json  # source/docs/data inventory snapshot
context-cache.json      # fingerprint metadata for safe cache reuse
context-pack.md         # compact Codex-first context summary
context-semantic-index.json # bounded symbol/term locator index
project-structure-completeness.md   # durable file structure, role map, and completion heuristic summary
project-structure-completeness.json # machine-readable companion for Pro review and automation
minimality_packet.json  # current minimal-solution ladder evidence
rdd-debt.jsonl          # append-only simplification debt ledger
todo_remain.jsonl       # append-only not-currently-executable TODOs moved out of the active completion loop
todo_archive/           # archived completed TODO event history plus archive manifests
pro-review/             # optional ChatGPT Pro review packets, responses, and TODO candidates
```

`todo_remain.jsonl` entries should include:

```json
{"id":"...","source_todo":"...","status":"deferred|blocked","reason":"...","required_dependency":"...","last_evidence":["..."],"resume_command_or_action":"...","timestamp":"YYYY-MM-DD"}
```

## Required references

Read these as needed:

```text
references/workflow.md
references/subagent-roles.md
references/model-routing.md
references/minimal-solution-policy.md
references/hook-policy.md
references/internal-skill-map.md
references/external-skill-links.md       # canonical external skill URL list
references/external-skills.md            # compatibility alias and external skill policy
references/external-skills.json          # machine-readable optional/required external skill registry
references/first-run-questionnaire.md
references/script-contracts.md          # generated script contract summary
references/function-scaffold.md          # function-by-function Python helper contract
references/codex-completion-and-registration.md
references/todo-policy.md
references/documentation-policy.md
references/state-schema.md
references/pro-review.md
```

## Helper scripts

The scripts are implemented helper contracts for inventory, requirement analysis, critic findings, TODO lifecycle, validation evidence, documentation checks, state, registration, and workflow preview. Use them to support the main-agent workflow; do not let scripts make final decisions or auto-accept critic findings.

```text
scripts/requirement_analyzer.py       # requirement packet and first response options
scripts/context_inventory.py          # source/docs/tests/data inventory, cache, context pack, semantic index, bootstrap
scripts/minimal_solution_ladder.py    # pre-TODO minimal solution ladder packet
scripts/diff_budget.py                # touched-file/LOC/abstraction/dependency budget
scripts/dependency_guard.py           # dependency addition diff guard
scripts/model_router.py               # custom-agent route and spawn-plan metadata
scripts/pro_review.py                 # optional agbrowse ChatGPT Pro context packet, recursive review, and TODO import
scripts/rdd_commands.py               # rdd-simplify/audit/debt/gain/spark-review helpers
scripts/external_skill_registry.py    # explicit external skill URLs and phase mapping
scripts/subagent_brief_builder.py     # critical-only subagent briefs
scripts/critic_ledger.py              # finding/decision ledger
scripts/todo_manager.py               # TODO JSONL lifecycle
scripts/quality_gate.py               # test/lint/build/eval evidence
scripts/doc_sync_check.py             # documentation sync checks
scripts/workflow_runner.py            # orchestration preview and safe state setup
scripts/rdd_state.py                  # persistent first-run/default state
scripts/validate_skill.py             # layout and syntax validation
scripts/self_test.py                  # end-to-end smoke workflow validation
scripts/skill_registration_helper.py # alternate registration helper
scripts/skill_registration.py        # optional Codex skill install helper
scripts/data_profile.py              # CSV/TSV/JSONL data profile for data critics
```

## External skill link policy

## Fast context policy

Prefer `.codex/review-driven-development/context-pack.md` as the first project reference after synchronization. Read its `Role map` section before opening source trees; it records responsibility boundaries and semantic-search query hints. Use `context-inventory.json` for structured file lists, `context-cache.json` for cache validity metadata, and `context-semantic-index.json` plus `--semantic-search` for fast file ranking. Default backend order is `scikit-learn` TF-IDF, then lexical overlap; use `--embeddings` only when dense ranking is worth the time/model-load cost. Open full source files only when the role map, compact pack, semantic search, or active TODO points to them.

Also read `.codex/review-driven-development/project-structure-completeness.md` after sync. It is the durable RDD summary of the current folder structure, inferred responsibilities, completeness checks, gaps, and review focus. The `agbrowse-chatgpt-pro-review` companion should use this file as primary evidence for improvement review.

For Pro feedback, run only once after the active TODO backlog is terminal, and use it to replenish TODOs rather than to critique every completed TODO. Always include `.codex/review-driven-development/project-structure-completeness.md` or a freshly generated context packet derived from it. The prompt should ask Pro to separate `locally_actionable_todos` from `external_or_manual_todos`, and to avoid proposing or implying real-money payment, cash-out, prizes, user trading, gambling-site integration, real horse-racing data, or actual betting advice.

For repo-local automatic guidance, write the marker-managed `AGENTS.md` bootstrap block. Re-running the command replaces only that block.

Useful commands:

```text
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --overview
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "<query>"
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --role-map
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --structure-completeness
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase overview
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-index
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-search --query "<query>"
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase role-map
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase structure-completeness
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase validation --todo-id "<id>" --agent-budget spark-first
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase pro-review --prompt "<review request>" --pro-review-no-add-todos
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase pro-review --prompt "<final review request>" --pro-review-recursive
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase commands
```

When invoking an external skill, consult `references/external-skill-links.md` or `references/external-skills.md` and prefer the explicit source URL listed there. Official OpenAI skills are preferred for OpenAI/Codex-specific behavior. Community skills must be treated as untrusted until their `SKILL.md`, scripts, and permissions are reviewed.

Optional companion skills, such as `agentic-rag`, may be used internally for domain-specific TODOs when they are present locally or listed in `references/external-skills.json`. Keep `review-driven-development` as the single user-facing workflow and record companion influence in the decision log.

## Language policy

- Primary response language: match the user.
- First-priority languages: Korean (`ko`) and English (`en`).
- Preserve identifiers, commands, API names, filenames, and error messages in original form.
- Store language defaults in `.codex/review-driven-development/defaults.json`.

## Exit condition

A default run may stop only when every TODO is one of:

```text
completed | blocked | deferred
```

An `until-complete` run may stop only when every TODO is either:

```text
completed
```

or recorded in:

```text
.codex/review-driven-development/todo_remain.jsonl
```

with a concrete non-executable reason and resume action.

and the final response includes:

```text
completed TODOs
remaining TODOs
todo_remain entries when any work was moved out of the active loop
validation evidence
documentation updates
accepted/rejected critique summary
next recommended TODO if work continues
```
