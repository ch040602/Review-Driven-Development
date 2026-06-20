# Workflow / 작업 흐름

## Phase 0. Intake and project state

1. Load `.codex/review-driven-development/defaults.json` if it exists.
2. If defaults are missing, gather context first, then ask first-run questions.
3. Save exact answers to `profile.md` and parsed defaults to `defaults.json`.

Helper scripts:

```text
rdd_state.py
context_inventory.py
requirement_analyzer.py
```

Fast context sync:

```text
context_inventory.py --sync
context_inventory.py --sync --semantic-summary
context_inventory.py --sync --semantic-search "<query>"
context_inventory.py --sync --bootstrap
workflow_runner.py --phase sync
workflow_runner.py --phase overview
workflow_runner.py --phase semantic-index
workflow_runner.py --phase semantic-search --query "<query>"
workflow_runner.py --phase bootstrap
workflow_runner.py --phase commands
```

`context-pack.md` should be the first Codex reference after sync. Use `--semantic-search "<query>"` to rank likely files, symbols, and terms before broad search. Ranking uses `sentence-transformers` embedding cosine when vectors are available, `scikit-learn` TF-IDF when installed, and lexical overlap otherwise. Use the full `context-inventory.json` or source files only when the pack, search result, or active TODO points to them. `--bootstrap` writes a marker-managed `AGENTS.md` block so future Codex sessions receive this policy automatically.

## Phase 1. Source/file-driven requirements analysis

Analyze:

```text
user prompt
uploaded/attached files
AGENTS.md
README*
docs/**/*.md
source files
tests
build/package files
CSV/log/data files
PDF/DOCX files if present through corresponding skills
```

Output:

```text
requirement packet
context-cache metadata
compact context pack
semantic locator index
repo-local bootstrap guidance when requested
language/runtime options with pros/cons
implementation method options with pros/cons
existing code reuse/review/refactor options with pros/cons
validation strategy options
documentation strategy options
```

## Phase 2. Parallel critical-only subagent debate

Spawn as many parallel critics as useful:

```text
requirements critic
language/runtime critic
architecture critic
existing-code reuse/refactor critic
test/TDD critic
security/risk critic
documentation critic
data/CSV critic
performance/efficiency critic
accuracy/evaluation critic
```

All subagents are critical-only. They return findings, not decisions.

Helper scripts:

```text
subagent_brief_builder.py
critic_ledger.py
```

## Phase 3. Main-agent decision and TODO generation

The main agent classifies every finding:

```text
accept
reject
defer
needs_user_input
```

Only accepted findings become TODO seeds.

Helper scripts:

```text
critic_ledger.py
todo_manager.py
```

## Phase 4. Sequential TODO execution

Rule: exactly one TODO may be `in_progress`.

Per TODO:

1. Confirm acceptance criteria.
2. Use `test-driven-development` where practical.
3. Implement the smallest complete vertical slice.
4. Run validation commands.
5. Use `systematic-debugging` or `debugging-and-error-recovery` if checks fail.

Helper scripts:

```text
todo_manager.py
quality_gate.py
workflow_runner.py
```

## Phase 5. Independent validation

A separate validation critic checks:

```text
diff/touched files
acceptance criteria
failing-then-passing evidence
lint/build/test/eval evidence
regression risk
missing tests
security concerns
documentation requirements
```

Helper scripts:

```text
subagent_brief_builder.py
critic_ledger.py
quality_gate.py
```

## Phase 6. Documentation

Before a TODO is completed, update one or more:

```text
README.md
docs/
docs/adr/
CHANGELOG.md
implementation-log.md
API docs
usage examples
```

Helper scripts:

```text
doc_sync_check.py
rdd_state.py
```

## Phase 7. Improvement critique

After validation and documentation, spawn critical-only improvement agents:

```text
quality critic
efficiency/performance critic
accuracy/evaluation critic
data/CSV critic
documentation critic
maintainability critic
```

Accepted improvements become new TODOs.

## Phase 8. TODO update and repeat

Update ledgers:

```text
todos.jsonl
critic-findings.jsonl
decision-log.md
review-ledger.md
implementation-log.md
```

Continue until all TODOs are `completed`, `blocked`, or `deferred`.
