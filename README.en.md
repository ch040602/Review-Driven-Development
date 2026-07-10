# review-driven-development

`review-driven-development` is a Codex custom skill for high-completeness development and research workflows. It packages critical review, TODO discipline, TDD validation, documentation, and improvement loops into a repeatable skill.

See the main [README.md](README.md) for the full GitHub-facing documentation. Korean documentation is available in [README.ko.md](README.ko.md).

## Install

```bash
mkdir -p .agents/skills
cp -R skills/review-driven-development .agents/skills/review-driven-development
python .agents/skills/review-driven-development/scripts/validate_skill.py \
  --skill-dir .agents/skills/review-driven-development
```

Then invoke in Codex:

```text
Use $review-driven-development for this requirement.
```

## Validate

```bash
python -m pip install -U pip pytest
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

Expected result:

```text
validate_skill.py: ok True
self_test.py: ok true
pytest: 14 passed
```

Optional semantic ranking dependency:

```bash
python -m pip install -e ".[semantic]"
python -m pip install -e ".[embeddings]"
# or both
python -m pip install -e ".[all]"
```

Fast context sync:

```bash
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --overview
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "quality gate completion"
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --role-map
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase commands
```

Codex should open `.codex/review-driven-development/context-pack.md` first, check its `Role map`, run one listed query hint with `--semantic-search "<query>"` when needed, then inspect only the files referenced by the active TODO. Default ranking uses `scikit-learn` TF-IDF when installed, then lexical overlap; add `--embeddings` only when dense `sentence-transformers` ranking is worth the model-load cost. `--sync --role-map` prints the responsibility map as JSON, and `--sync --bootstrap` writes a marker-managed `AGENTS.md` block for future Codex sessions.

Subagent routing is data-driven through `references/model-routing-policy.json`. The bundled catalog contains only `gpt-5.3-codex-spark` and `gpt-5.6`: simple/local implementation uses Spark `low`, structured critics use Spark `medium`, additional logic or cross-file reasoning uses GPT-5.6 `high`, and explicit deep security/data/architecture review uses GPT-5.6 `max`. Runtime availability and route/plan budgets are hard gates; an unsatisfied `high`/`max` request is never silently downgraded. Use `model_router.py --list-models` to inspect the catalog and repeated `--available-model` flags to constrain a run.

Default `self_test.py` avoids embedding model loading for CI stability. Run the heavier embedding smoke check explicitly:

```bash
python skills/review-driven-development/scripts/self_test.py --embeddings
```

Set `HF_TOKEN` for higher Hugging Face rate limits when using `--embeddings`. In offline or restricted environments use the default non-embedding path, `--force-tfidf`, or `--force-lexical`.

## GitHub

This package includes GitHub Actions CI, Dependabot, issue templates, a PR template, CODEOWNERS, and community files. Before publishing, replace `YOUR_GITHUB_USERNAME` and add a license.
