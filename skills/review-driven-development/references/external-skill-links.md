# External skill links / 외부 skill 링크

Use this file whenever `review-driven-development` invokes or recommends an external skill. Prefer pinned commits or reviewed local copies for production use.

## Trust tiers

| Tier | Meaning |
|---|---|
| `official-openai` | OpenAI-maintained or OpenAI-documented; preferred for Codex/OpenAI-specific workflows |
| `community-reviewed` | Third-party/community source; inspect `SKILL.md`, scripts, hooks, permissions before use |
| `local-current` | Already present in the user's current skill inventory; no public link asserted unless known |
| `optional-missing` | Referenced by this workflow but not assumed installed |

## Official OpenAI skills and docs

| Skill/doc | Use in this project | Link |
|---|---|---|
| Codex Agent Skills docs | Skill structure, registration locations, progressive loading | https://developers.openai.com/codex/skills |
| Codex Subagents docs | Parallel subagent workflow design | https://developers.openai.com/codex/subagents |
| Codex AGENTS.md docs | Project instruction discovery and persistent repo guidance | https://developers.openai.com/codex/guides/agents-md |
| Codex GitHub code review docs | `@codex review`, automatic review, review guidelines | https://developers.openai.com/codex/integrations/github |
| OpenAI skills catalog | Official/curated/experimental skill catalog | https://github.com/openai/skills |
| `skill-creator` | Create or refine custom skills | https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md |
| `define-goal` | Convert vague requirements into measurable objectives | https://github.com/openai/skills/blob/main/skills/.curated/define-goal/SKILL.md |
| `create-plan` | Structured planning; experimental, verify before production use | https://github.com/openai/skills/blob/main/skills/.experimental/create-plan/SKILL.md |
| `gh-address-comments` | Import and address GitHub PR comments as review/TODO inputs | https://github.com/openai/skills/blob/main/skills/.curated/gh-address-comments/SKILL.md |
| `openai-docs` | OpenAI/Codex/API documentation grounding | https://github.com/openai/skills/blob/main/skills/.curated/openai-docs/SKILL.md |

## Community engineering workflow skills

| Skill | Use in this project | Link |
|---|---|---|
| `using-agent-skills` | Meta skill selection and phase mapping | https://github.com/addyosmani/agent-skills/blob/main/skills/using-agent-skills/SKILL.md |
| `spec-driven-development` | Turn requirements into a concrete spec before code | https://github.com/addyosmani/agent-skills/blob/main/skills/spec-driven-development/SKILL.md |
| `planning-and-task-breakdown` | Break accepted findings/spec into small verifiable TODOs | https://github.com/addyosmani/agent-skills/blob/main/skills/planning-and-task-breakdown/SKILL.md |
| `incremental-implementation` | Implement one vertical slice at a time | https://github.com/addyosmani/agent-skills/blob/main/skills/incremental-implementation/SKILL.md |
| `source-driven-development` | Ground implementation decisions in official sources/docs | https://github.com/addyosmani/agent-skills/blob/main/skills/source-driven-development/SKILL.md |
| `test-driven-development` | Red/green/refactor and validation evidence | https://github.com/addyosmani/agent-skills/blob/main/skills/test-driven-development/SKILL.md |
| `debugging-and-error-recovery` | Reproduce, localize, fix, and guard against failures | https://github.com/addyosmani/agent-skills/blob/main/skills/debugging-and-error-recovery/SKILL.md |
| `code-review-and-quality` | Review gate before completion/merge | https://github.com/addyosmani/agent-skills/blob/main/skills/code-review-and-quality/SKILL.md |
| `code-simplification` | Behavior-preserving refactor and simplification | https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md |
| `documentation-and-adrs` | README/API/ADR/changelog discipline | https://github.com/addyosmani/agent-skills/blob/main/skills/documentation-and-adrs/SKILL.md |
| `security-and-hardening` | Security review and hardening critique | https://github.com/addyosmani/agent-skills/blob/main/skills/security-and-hardening/SKILL.md |
| `performance-optimization` | Performance/efficiency critique | https://github.com/addyosmani/agent-skills/blob/main/skills/performance-optimization/SKILL.md |
| `api-and-interface-design` | API boundary and interface critique | https://github.com/addyosmani/agent-skills/blob/main/skills/api-and-interface-design/SKILL.md |

## Local skills from the current inventory

The following names came from the user's current skill list. Use them when they exist locally. Do not infer a public URL unless the user provides it or it is added here after review.

```text
paper-summary-agent
research-idea-consensus
prompt-graph-manager
hatch-pet
awesome-design-md
csv-data-summarizer
docx
frontend-slides
ios-simulator-skill
pdf
subagent-driven-development
systematic-debugging
test-driven-development
webapp-testing
```

## Invocation rule

When a workflow step says “use external skill X,” Codex should:

1. Check whether X exists locally.
2. If missing, consult this file and decide whether to install/copy from the link.
3. Prefer official OpenAI skills for OpenAI/Codex functions.
4. For third-party skills, inspect `SKILL.md`, scripts, and permissions before using.
5. If no safe external skill is available, use the fallback instructions in `internal-skill-map.md` and record that fallback in `decision-log.md`.
