# GitHub setup guide

This guide covers the repository settings recommended for publishing `review-driven-development` on GitHub.

## 1. Replace placeholders

```bash
grep -R "YOUR_GITHUB_USERNAME" -n .
grep -R "@YOUR_GITHUB_USERNAME" -n .
```

Update:

- `README.md`
- `README.ko.md`
- `README.en.md`
- `.github/CODEOWNERS`
- `.github/ISSUE_TEMPLATE/config.yml`

## 2. Create the repository

```bash
git init
git add .
git commit -m "Initial review-driven-development skill"
gh repo create review-driven-development --public --source=. --remote=origin --push
```

Use `--private` instead of `--public` if needed.

## 3. GitHub Actions

The CI workflow lives at:

```text
.github/workflows/ci.yml
```

It validates:

- helper script syntax
- skill layout
- registration helper
- `self_test.py`
- pytest smoke tests

## 4. Dependabot

Dependabot config lives at:

```text
.github/dependabot.yml
```

It currently checks GitHub Actions updates weekly. Add Python package ecosystem entries only if the project starts using dependency manifests.

## 5. Branch protection / rulesets

Recommended settings for `main`:

- Require a pull request before merging.
- Require at least one approval.
- Require status checks to pass.
- Require conversation resolution.
- Block force pushes.
- Block branch deletion.
- Require CODEOWNERS review if you want stricter ownership.

## 6. Security settings

Recommended:

- Enable Dependabot alerts.
- Enable Dependabot security updates.
- Enable private vulnerability reporting if this is public.
- Keep Actions permissions read-only unless a workflow needs write access.

## 7. License

No open-source license is selected by default. Add a `LICENSE` file before making the repository public if you want others to use, modify, or redistribute the project under defined terms.

## 8. First release checklist

- [ ] CI passes on `main`.
- [ ] README badges point to the real repository.
- [ ] `VALIDATION.md` is current.
- [ ] `external-skills.json` and reference Markdown files are consistent.
- [ ] Codex recognizes `$review-driven-development` via `/skills`.
- [ ] A release tag is created if needed.
