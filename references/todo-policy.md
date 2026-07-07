# TODO policy

## Statuses

```text
pending
in_progress
blocked
completed
deferred
```

## Hard rules

1. Exactly one TODO may be `in_progress`.
2. Every TODO must have acceptance criteria before implementation.
3. Every behavior-changing TODO should use `test-driven-development` when practical.
4. A TODO cannot be `completed` unless it has:
   - validation evidence
   - independent validation/review reference
   - documentation reference or explicit `not_needed` rationale
   - no unresolved blocker/high accepted finding
5. Improvement findings after a TODO become new TODOs only if accepted by the main agent.

## Completed TODO archival

Completed TODO history should leave the active ledger immediately. Prefer the
normal completion command:

```bash
python scripts/todo_manager.py --root . complete RDD-T-00000001
```

By default, completion writes full completed TODO events to
`.codex/review-driven-development/todo_archive/` and rewrites `todos.jsonl`
with non-completed events plus a compact `archive_stub` record for the completed
TODO ID. Use `--keep-in-ledger` only when debugging the ledger.

For older or manually edited ledgers, compact completed history explicitly:

```bash
python scripts/todo_manager.py --root . archive-completed
```

The stubs must keep `status: completed` so dependency checks and
terminal-backlog checks remain correct without reloading full history. The
default `list` command omits completed stubs; pass `--include-completed` when
auditing terminal TODOs.

## Recommended TODO shape

```text
small enough for one focused implementation slice
large enough to produce user-visible or test-visible value
explicit dependencies
explicit validation command or evidence
explicit documentation requirement
```
