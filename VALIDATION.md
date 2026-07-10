# Validation evidence

## 2026-07-10 capability-based model routing update

Commands:

```bash
python -m pytest -q
python scripts/self_test.py
python scripts/validate_skill.py --skill-dir .
python -m compileall -q -f scripts
python -m ruff check scripts/model_router.py scripts/subagent_brief_builder.py scripts/validate_skill.py scripts/workflow_runner.py tests/test_model_router.py tests/test_smoke_workflow.py tests/test_spark_agent_config.py
python scripts/model_router.py --list-models
python scripts/model_router.py --phase execution --task-kind simple-implementation
python scripts/model_router.py --phase execution --task-kind logic-design
python scripts/model_router.py --phase preplan --role security-risk-critic --critic-depth deep --agent-budget deep
```

Observed result:

```text
pytest: 71 passed
self_test.py: ok true
Skill validation report: ok True
compileall: passed
Ruff on changed Python/test files: passed
catalog: gpt-5.3-codex-spark, gpt-5.6 only
simple implementation: gpt-5.3-codex-spark / low
logic design: gpt-5.6 / high
deep security critic: gpt-5.6 / max
```

Coverage includes policy-schema validation, catalog substitution without code changes, runtime availability filtering, explicit unavailable/budget-limited statuses, no silent `max` downgrade, bounded fallback candidates, aggregate spawn-plan budget enforcement, workflow propagation (including explicit execution-phase implementation routes), static custom-agent model/effort matching, and default-critical versus explicitly bounded-implementation hook behavior.

Repository-wide Ruff still reports the pre-existing unused `typing.Iterable` import in `scripts/diff_budget.py`; that unrelated file was not changed by this routing update.

Validation performed after README and GitHub repository polish.

## Static validation

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "quality gate completion" --top-k 5
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase overview
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-index
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase semantic-search --query "semantic search ranking backend" --top-k 5
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase bootstrap
python skills/review-driven-development/scripts/skill_registration.py --repo-root . --validate-only
python skills/review-driven-development/scripts/skill_registration_helper.py --skill-dir skills/review-driven-development --validate
```

Observed result:

```text
compile_ok
context_inventory.py: sync summary emitted
context_inventory.py: semantic summary/search emitted and AGENTS.md bootstrap written
workflow_runner.py: overview emitted context-pack payload
workflow_runner.py: semantic-index, semantic-search, and bootstrap phases emitted bounded metadata
semantic summary: ranking_backend embedding-cosine after installing `.[embeddings]`
Skill validation report: ok True
skill_registration.py: VALID
skill_registration_helper.py: valid true
```

## Behavioral smoke validation

```bash
python skills/review-driven-development/scripts/self_test.py
python skills/review-driven-development/scripts/self_test.py --embeddings
pytest -q
```

Observed result:

```text
self_test.py: ok true
self_test.py --embeddings: ok true
pytest: 14 passed
```

## What this proves

- `SKILL.md` layout and metadata are valid.
- Python helper scripts compile.
- Registration helper validates the skill folder.
- First-run default detection works.
- Context inventory can write reusable `context-cache.json` and compact `context-pack.md`.
- Context inventory can write bounded `context-semantic-index.json`.
- Semantic search uses dense `sentence-transformers` embeddings when vectors are available, `scikit-learn` TF-IDF when available, and lexical fallback when forced/unavailable.
- Default `self_test.py` avoids embedding model loading; `self_test.py --embeddings` covers the heavier embedding path explicitly.
- Context inventory can inject a marker-managed `AGENTS.md` fast-context block.
- `workflow_runner.py` exposes `sync`, `overview`, `semantic-index`, `bootstrap`, and `commands` phases for fast Codex reference.
- Accepted critic findings can become TODOs.
- One active TODO can be started.
- Validation/improvement phases are not generated before implementation.
- Quality-gate evidence can be saved and linked to the TODO ledger.
- If real commands are configured in `commands.json` or parsed defaults, dry-run quality-gate evidence alone cannot complete a TODO.
- Independent review evidence can be recorded through CLI.
- Documentation status can be recorded through CLI.
- TODO completion gate completes only after evidence/review/docs requirements are satisfied.
- Unresolved blocker/high review findings block completion.
- Resolved, rejected, or deferred blocker/high review findings do not block completion.
- External skill URLs are checked offline across `external-skills.json`, `references/external-skills.md`, and `references/external-skill-links.md`.

## GitHub packaging validation

The updated package includes:

```text
.github/workflows/ci.yml
.github/dependabot.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/ISSUE_TEMPLATE/*.yml
.github/CODEOWNERS
CONTRIBUTING.md
SECURITY.md
SUPPORT.md
CODE_OF_CONDUCT.md
GITHUB_UPLOAD_CHECKLIST.md
docs/github-setup.md
pyproject.toml
```

## What this does not prove

- It does not prove that a real Codex subagent was spawned; scripts generate briefs and ledgers.
- It does not prove external/community skill installation; links and policy are present, but installation remains explicit.
- It does not prove project-specific tests pass until `commands.json` contains real test/lint/build/eval commands.
- It does not prove GitHub branch protection is enabled; that must be configured in the GitHub repository settings.

## Repo-local installation validation procedure

```bash
mkdir -p .agents/skills
cp -R skills/review-driven-development .agents/skills/review-driven-development
python skills/review-driven-development/scripts/skill_registration.py --scope repo --overwrite
```

Then open Codex in that repository and run `/skills` to confirm `review-driven-development` appears.
