---
name: review-driven-development
description: Use this skill for high-completeness software/research development. It analyzes requirements and source/docs/files, asks first-run defaults, uses critical-only subagents, turns accepted findings into TODOs, executes one TODO at a time, validates with test-driven-development, documents completed work, and repeats improvement review. Supports Korean and English.
---

# review-driven-development

## Mission

Run one integrated workflow:

```text
requirements -> first-run defaults -> source/file analysis -> parallel critical subagents -> main-agent decisions -> TODO plan -> one TODO execution -> TDD validation -> independent critical review -> documentation -> improvement critique -> TODO update -> repeat
```

Optimize for completeness, correctness, maintainability, traceability, and research usefulness over speed.

## Non-negotiable rules

1. Keep this as one user-facing skill: `review-driven-development`.
2. Use other skills only internally and record where they influenced the decision.
3. On first use in a project, ask `references/first-run-questionnaire.md` questions and save exact answers.
4. Persist defaults under `.codex/review-driven-development/` and use them silently on later runs unless the user overrides them.
5. Analyze prompt text, attached files, Markdown docs, `AGENTS.md`, source files, tests, build files, and data files before planning.
6. If existing code exists, ask whether to reuse, review, refactor, replace, isolate, or decide per TODO. If defaults exist, follow the saved policy.
7. Use subagents aggressively where work can be parallelized.
8. Debate, validation, review, and improvement subagents are **critical-only**: they identify risks and missing evidence; they do not decide or patch.
9. The main agent alone classifies feedback as `accept`, `reject`, `defer`, or `needs_user_input`.
10. Only accepted feedback becomes TODOs.
11. Keep exactly one TODO as `in_progress`.
12. Use `test-driven-development` for behavior changes and validation. When practical, write or update a failing test before implementation.
13. Use `systematic-debugging` for failed checks before broad changes.
14. Do not mark a TODO completed until evidence, validation notes, review notes, and documentation status are recorded.
15. After each TODO, run an improvement critique focused on quality, efficiency, accuracy, data correctness, documentation, and maintainability.

## Required state files

Create or update this directory in the target project:

```text
.codex/review-driven-development/
```

Minimum files:

```text
profile.md              # exact first-run answers and project assumptions
defaults.json           # parsed defaults used when no new instruction is provided
todos.jsonl             # append-only TODO lifecycle ledger
critic-findings.jsonl   # append-only critical subagent findings
decision-log.md         # accepted/rejected/deferred findings
review-ledger.md        # review and validation summaries
implementation-log.md   # completed work, evidence, docs status
commands.json           # test/lint/build/eval commands when known
context-inventory.json  # source/docs/data inventory snapshot
```

## Required references

Read these as needed:

```text
references/workflow.md
references/subagent-roles.md
references/internal-skill-map.md
references/external-skill-links.md       # canonical external skill URL list
references/external-skills.md            # compatibility alias and external skill policy
references/first-run-questionnaire.md
references/script-contracts.md          # generated script contract summary
references/function-scaffold.md          # function-by-function Python helper contract
references/codex-completion-and-registration.md
references/todo-policy.md
references/documentation-policy.md
references/state-schema.md
```

## Helper scripts

The scripts are implemented helper contracts for inventory, requirement analysis, critic findings, TODO lifecycle, validation evidence, documentation checks, state, registration, and workflow preview. Use them to support the main-agent workflow; do not let scripts make final decisions or auto-accept critic findings.

```text
scripts/requirement_analyzer.py       # requirement packet and first response options
scripts/context_inventory.py          # source/docs/tests/data inventory
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

When invoking an external skill, consult `references/external-skill-links.md` or `references/external-skills.md` and prefer the explicit source URL listed there. Official OpenAI skills are preferred for OpenAI/Codex-specific behavior. Community skills must be treated as untrusted until their `SKILL.md`, scripts, and permissions are reviewed.

## Language policy

- Primary response language: match the user.
- First-priority languages: Korean (`ko`) and English (`en`).
- Preserve identifiers, commands, API names, filenames, and error messages in original form.
- Store language defaults in `.codex/review-driven-development/defaults.json`.

## Exit condition

A run may stop only when every TODO is one of:

```text
completed | blocked | deferred
```

and the final response includes:

```text
completed TODOs
remaining TODOs
validation evidence
documentation updates
accepted/rejected critique summary
next recommended TODO if work continues
```
