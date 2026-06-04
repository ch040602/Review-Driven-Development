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
pytest: 11 passed
```

## GitHub

This package includes GitHub Actions CI, Dependabot, issue templates, a PR template, CODEOWNERS, and community files. Before publishing, replace `YOUR_GITHUB_USERNAME` and add a license.
