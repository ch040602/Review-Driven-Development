# Review notes for review-driven-development

## Verdict

The repository is now a usable Codex skill package for pre-operational use. It has a valid `SKILL.md`, references, helper scripts, external skill links, bilingual README files, static validation, and behavioral smoke tests.

However, the original validation was mostly static. It proved syntax and required-file presence, but did not fully prove the workflow loop.

## Issues found

| Issue | Severity | Impact | Fix applied |
|---|---:|---|---|
| `workflow_runner.run_once` prepared validation, documentation, and improvement phases immediately after starting a TODO | High | Could make Codex appear to validate/review before implementation evidence exists | Changed `run_once` to stop after starting the active TODO and return explicit post-implementation commands |
| TODO completion required independent review evidence, but CLI had no direct way to record a review pass | High | CLI-only smoke workflow could not complete a TODO without editing JSONL manually | Added `todo_manager.py review` and `add_review_record()` |
| `quality_gate.py` saved reports but did not link them to TODO validation evidence | Medium | Validation evidence existed as a file but the TODO ledger did not know about it | Added `--record-todo-evidence` and `record_report_as_todo_evidence()` |
| Dry-run quality-gate evidence could satisfy TODO completion even when real commands were configured | High | A TODO could be marked complete without running configured tests/lint/build/eval | Completion now requires executed passing `quality_gate` evidence when commands exist |
| blocker/high review finding resolution semantics needed regression tests | High | Unresolved critical review findings could regress silently | Added pytest cases for unresolved and resolved/rejected/deferred blocker/high findings |
| External skill URL drift needed offline coverage | Medium | Registry and Markdown references could diverge without network access | Added offline consistency test for `external-skills.json`, `external-skills.md`, and `external-skill-links.md` |
| `start_next_todo()` returned only the status event, not the materialized TODO | Medium | Workflow phase could lose acceptance criteria/expected files/docs metadata | Changed it to return the materialized TODO after status update |
| No behavioral test existed beyond compile/layout checks | High | Workflow could regress while static validation still passed | Added `self_test.py` and `tests/test_smoke_workflow.py` |
| Uploaded ZIP contained `.pytest_cache` | Low | Unnecessary artifact noise | Removed from final package and updated `.gitignore` |

## Behavioral workflow now tested

The new smoke test verifies:

1. First run asks for defaults before planning.
2. First-run answers are persisted.
3. Accepted critic finding becomes a TODO.
4. Exactly one TODO starts as `in_progress`.
5. Validation/improvement do not run before implementation.
6. Quality gate report can be linked to TODO evidence.
7. Independent review evidence can be recorded.
8. Documentation status can be recorded.
9. TODO completion gate succeeds only after evidence/review/docs gates are satisfied.
10. Validation and improvement critic briefs are generated explicitly after implementation.
11. Dry-run quality-gate evidence cannot complete a TODO when real commands are configured.
12. Unresolved blocker/high review findings block completion; resolved/rejected/deferred ones allow completion.
13. External skill URLs remain consistent across JSON and Markdown references without network access.

## Remaining intentional limitations

- The scripts do not launch real Codex subagents. They generate subagent briefs and ledgers; the Codex main agent must spawn subagents.
- The scripts do not edit product source code. Implementation remains the main agent’s job.
- `test-driven-development` is invoked as workflow instruction, not embedded as a Python test generator.
- External/community skills are linked and gated by inspection policy, but not automatically downloaded.
