# ChatGPT Pro Review Loop

Use this reference only when the user explicitly requests ChatGPT Pro, Pro review,
external AI feedback, recursive review, or `--pro-review`, and only after active
RDD TODOs are completed, blocked, or deferred. Do not use it as an automatic
per-TODO, post-validation, or improvement-loop critic.

## Purpose

The Pro review loop asks ChatGPT Pro to critique the current implementation,
file structure, inferred roles, and completeness gaps from RDD context packets.
It is a TODO replenishment step, not an implementation agent and not a recurring
critic after every TODO.

Before every live or dry-run review, RDD sync refreshes:

```text
.codex/review-driven-development/project-structure-completeness.md
.codex/review-driven-development/project-structure-completeness.json
```

Treat `project-structure-completeness.md` as the primary structure/role/completeness
artifact for Pro review. The Pro packet attaches it when present and also records
its JSON-derived score in `context.md` and `context.yaml`.

## Commands

Dry run, no provider call and no TODO import:

```text
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase pro-review --prompt "<review request>" --pro-review-dry-run --pro-review-no-add-todos
```

One live Pro review, store candidates but do not append TODOs. This is allowed
only when no active TODO is pending or in progress:

```text
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase pro-review --prompt "<review request>" --pro-review-no-add-todos
```

One live Pro review and append TODOs. This is allowed only when no active TODO
is pending or in progress:

```text
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase pro-review --prompt "<review request>"
```

Final recursive live review, after all active RDD TODOs are completed, blocked,
or deferred. This is limited to one live provider round and should replenish the
backlog only when it finds concrete locally actionable TODOs:

```text
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase pro-review --prompt "<final review request>" --pro-review-recursive
```

Do not run recursive Pro review through `--phase once`; that path defers the
provider call until the active backlog is terminal.

```text
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase once --prompt "<requirement>" --pro-review --pro-review-recursive
```

## Artifacts

Each round writes:

```text
.codex/review-driven-development/pro-review/<timestamp>-round-001/context.md
.codex/review-driven-development/pro-review/<timestamp>-round-001/context.yaml
.codex/review-driven-development/pro-review/<timestamp>-round-001/prompt.md
.codex/review-driven-development/project-structure-completeness.md
.codex/review-driven-development/pro-review/<timestamp>-round-001/agbrowse-result.json
.codex/review-driven-development/pro-review/<timestamp>-round-001/response.md
.codex/review-driven-development/pro-review/<timestamp>-round-001/todo-candidates.json
```

`context.md` is human-readable. `context.yaml` is machine-readable enough for
Pro to inspect file categories, role map entries, current TODOs, Git state, and
the current structure/completeness packet. The Markdown structure file remains
the easier artifact for model review.

## TODO Import Policy

- Imported TODOs are pending RDD TODOs with `source_finding_id` set to the round
  artifact directory.
- The main agent still executes exactly one TODO at a time.
- Live Pro review is blocked while any TODO is `pending` or `in_progress`.
- Recursive mode is final-only and runs at most one live provider round per RDD
  run, after active TODOs are terminal. Newly imported TODOs are queued for a
  subsequent normal RDD loop unless the user explicitly starts that loop.
- Use `--pro-review-no-add-todos` when the main agent should inspect and decide
  before importing.
- Use `--todo-limit N` on `scripts/pro_review.py` directly if a run returns too
  many items.

## Preconditions

- `agbrowse` must be installed and on PATH.
- `agbrowse start --headed` must be able to control a local Chrome profile.
- ChatGPT must be logged in inside the agbrowse Chrome profile.
- Use the companion `agbrowse-chatgpt-pro-review` skill for direct provider
  commands and troubleshooting.
