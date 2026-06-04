# Security Policy

## Supported versions

This repository is currently a draft skill package. Security fixes should target `main` unless release branches are introduced later.

## Reporting a vulnerability

Please do not open a public issue for sensitive vulnerabilities. Use the repository's private vulnerability reporting feature if enabled, or contact the maintainer listed in the repository profile.

## Security expectations

- Do not commit secrets, API keys, tokens, private datasets, or credentials.
- Do not store secrets in `.codex/review-driven-development/` state files.
- Review community/third-party skills before enabling scripts, hooks, or permissions.
- Treat external skill repositories and generated scripts as code that must be reviewed.
- Destructive changes, dependency upgrades, and migrations should require explicit user confirmation in the skill workflow.

## Scope

Security issues may include:

- Unsafe command execution in helper scripts
- Accidental secret persistence in state files
- Unreviewed external skill execution
- Weakening TODO completion or review gates in a way that hides unsafe changes
