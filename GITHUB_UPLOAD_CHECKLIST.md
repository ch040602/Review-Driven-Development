# GitHub Upload Checklist

## Before first push

- [ ] Replace `YOUR_GITHUB_USERNAME` placeholders.
- [ ] Replace `.github/CODEOWNERS` owner.
- [ ] Decide repository visibility: public or private.
- [ ] Add a `LICENSE` file if this will be open source.
- [ ] Review external skill links in `external-skills.json` and `references/external-skills.md`.
- [ ] Run local validation.

```bash
grep -R "YOUR_GITHUB_USERNAME" -n .
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

## First push

```bash
git init
git add .
git commit -m "Initial review-driven-development skill"
gh repo create review-driven-development --public --source=. --remote=origin --push
```

For private repositories:

```bash
gh repo create review-driven-development --private --source=. --remote=origin --push
```

## After push

- [ ] Confirm GitHub Actions CI runs.
- [ ] Enable branch protection or repository rulesets for `main`.
- [ ] Require CI status checks before merge.
- [ ] Require at least one PR review.
- [ ] Require conversation resolution before merge.
- [ ] Enable Dependabot security alerts and version updates.
- [ ] Confirm `/skills` recognizes the skill after repository-local install.

## Recommended repository topics

```text
codex skill agentic-workflow tdd code-review automation developer-tools python
```
