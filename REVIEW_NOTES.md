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
| Context analysis required reopening broad source/docs on every run | Medium | Codex could waste context and latency re-reading files already summarized | Added fingerprinted `context-cache.json`, compact `context-pack.md`, and `sync/overview/commands` workflow phases |
| Fast context policy still required the user to remember commands | Medium | New Codex sessions could skip the compact pack and semantic locator | Added marker-managed `AGENTS.md` bootstrap plus bounded `context-semantic-index.json` |
| Semantic locator used only lexical/symbol overlap | Medium | Related files could rank poorly when the query used different wording | Added optional `scikit-learn` TF-IDF ranking with lexical fallback |
| TF-IDF still missed deeper paraphrase similarity | Medium | Queries using different vocabulary could miss relevant files | Added optional `sentence-transformers` dense embedding vectors with cosine ranking before TF-IDF fallback |
| Default smoke test loaded embedding models after embeddings extra was installed | Medium | CI or offline runs could become slow or flaky | Made embedding smoke validation explicit with `self_test.py --embeddings`; default smoke uses non-embedding backend |
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
14. Context sync writes a bounded reusable cache and compact context pack.
15. Workflow runner exposes fast `sync`, `overview`, and `commands` UX.
16. Bootstrap writes repo-local fast-context guidance into `AGENTS.md`.
17. Semantic locator index records bounded terms and shallow symbols for targeted file lookup.
18. Semantic search ranks files with `scikit-learn` TF-IDF when available and lexical fallback otherwise.
19. Semantic search ranks files with `sentence-transformers` embeddings when vectors are available, before TF-IDF fallback.
20. Default smoke validation avoids embedding model loading; embedding smoke is explicit opt-in.

## Remaining intentional limitations

- The scripts do not launch real Codex subagents. They generate subagent briefs and ledgers; the Codex main agent must spawn subagents.
- The scripts do not edit product source code. Implementation remains the main agent’s job.
- `test-driven-development` is invoked as workflow instruction, not embedded as a Python test generator.
- External/community skills are linked and gated by inspection policy, but not automatically downloaded.
- The context cache uses path/size/mtime metadata. Semantic search can use dense embeddings when `sentence-transformers` is installed, but it remains a locator; Codex should still open source files referenced by the active TODO before editing.
- `.codex/` state is local-only and ignored by Git. Rebuild it with `context_inventory.py --sync` after clone/install.
