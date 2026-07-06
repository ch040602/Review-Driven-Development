# Hook policy

RDD repo-local hooks are advisory guardrails for high-cost mistakes. They should not make normal Codex usage noisy.

| Hook | Purpose |
|---|---|
| `SessionStart` | Remind the agent to read compact context and use the minimality gate. |
| `PreToolUse` | Block dependency install commands and destructive commands until explicit evidence or user confirmation exists. |
| `PostToolUse` | Remind the agent to run diff budget and validation evidence after edits. |
| `SubagentStart` | Reinforce critical-only, no-patch, minimal-change review behavior. |
| `Stop` | Warn if validation, review, docs, or blocker/high decision gates may be missing. |

Repo-local hooks require trust review before enabling in a target project. Keep blockers limited to dependency additions, destructive commands, and missing completion evidence.
