#!/usr/bin/env python3
"""External skill registry for review-driven-development.

Role in the skill
-----------------
This module keeps external skill links in executable, inspectable form. The
Markdown source of truth is ``references/external-skills.md``; this script mirrors
those entries so Codex can render install instructions or select phase-specific
skills.

Completion guidance for Codex
-----------------------------
- Do not invent external skill URLs.
- Update both this file and ``references/external-skills.md`` when links change.
- Treat third-party skills as inspect-before-use. Read SKILL.md, scripts, hooks,
  and license before using them in implementation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class ExternalSkill:
    """A skill dependency or recommended external workflow."""

    name: str
    provider: str
    url: str
    required: bool
    phase: str
    purpose: str
    install_hint: str
    inspect_before_use: bool = True


OPENAI_SKILLS_REPO = "https://github.com/openai/skills"
OPENAI_SKILLS_DOCS = "https://developers.openai.com/codex/skills"
ADDY_AGENT_SKILLS_REPO = "https://github.com/addyosmani/agent-skills"

EXTERNAL_SKILLS: List[ExternalSkill] = [
    ExternalSkill(
        name="OpenAI Codex Agent Skills docs",
        provider="openai-docs",
        url=OPENAI_SKILLS_DOCS,
        required=True,
        phase="registration",
        purpose="Canonical skill format, save locations, activation behavior, and registration guidance.",
        install_hint="Read only; not installed as a skill.",
        inspect_before_use=False,
    ),
    ExternalSkill(
        name="Codex Subagents docs",
        provider="openai-docs",
        url="https://developers.openai.com/codex/subagents",
        required=True,
        phase="subagents",
        purpose="Parallel subagent workflow design and delegation constraints.",
        install_hint="Read only; not installed as a skill.",
        inspect_before_use=False,
    ),
    ExternalSkill(
        name="Codex AGENTS.md docs",
        provider="openai-docs",
        url="https://developers.openai.com/codex/guides/agents-md",
        required=True,
        phase="context",
        purpose="Project instruction discovery and persistent repository guidance.",
        install_hint="Read only; not installed as a skill.",
        inspect_before_use=False,
    ),
    ExternalSkill(
        name="Codex GitHub code review docs",
        provider="openai-docs",
        url="https://developers.openai.com/codex/integrations/github",
        required=False,
        phase="review-comments",
        purpose="Codex GitHub review behavior and review guideline grounding.",
        install_hint="Read only; not installed as a skill.",
        inspect_before_use=False,
    ),
    ExternalSkill(
        name="OpenAI skills catalog",
        provider="openai",
        url=OPENAI_SKILLS_REPO,
        required=True,
        phase="installation",
        purpose="Official catalog for curated/system/experimental Codex skills.",
        install_hint="$skill-installer <skill-name> or $skill-installer install <GitHub directory URL>",
        inspect_before_use=False,
    ),
    ExternalSkill(
        name="skill-creator",
        provider="openai",
        url="https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md",
        required=False,
        phase="skill-authoring",
        purpose="Create or refine custom skills.",
        install_hint="$skill-installer skill-creator when not already installed.",
    ),
    ExternalSkill(
        name="gh-address-comments",
        provider="openai",
        url="https://github.com/openai/skills/blob/main/skills/.curated/gh-address-comments/SKILL.md",
        required=True,
        phase="review-comments",
        purpose="Read unresolved GitHub PR review comments and convert accepted feedback into TODOs.",
        install_hint="$skill-installer gh-address-comments",
    ),
    ExternalSkill(
        name="define-goal",
        provider="openai",
        url="https://github.com/openai/skills/blob/main/skills/.curated/define-goal/SKILL.md",
        required=True,
        phase="goal-definition",
        purpose="Turn broad requirements into measurable objectives, constraints, and stop conditions.",
        install_hint="$skill-installer define-goal",
    ),
    ExternalSkill(
        name="create-plan",
        provider="openai-experimental",
        url="https://github.com/openai/skills/blob/main/skills/.experimental/create-plan/SKILL.md",
        required=False,
        phase="planning",
        purpose="Create a structured implementation plan before TODO creation; experimental output must be reviewed critically.",
        install_hint="$skill-installer install https://github.com/openai/skills/tree/main/skills/.experimental/create-plan",
    ),
    ExternalSkill(
        name="openai-docs",
        provider="openai",
        url="https://github.com/openai/skills/blob/main/skills/.curated/openai-docs/SKILL.md",
        required=False,
        phase="source-grounding",
        purpose="Ground OpenAI API, Codex, and Agents SDK decisions in official OpenAI docs.",
        install_hint="$skill-installer openai-docs",
    ),
    ExternalSkill(
        name="using-agent-skills",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/using-agent-skills/SKILL.md",
        required=False,
        phase="skill-selection",
        purpose="Meta skill selection and phase mapping.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="spec-driven-development",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/spec-driven-development/SKILL.md",
        required=False,
        phase="requirements",
        purpose="Turn requirements into a concrete spec before code.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="source-driven-development",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/source-driven-development/SKILL.md",
        required=True,
        phase="source-grounding",
        purpose="Ground framework/library decisions in official documentation and source evidence.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="planning-and-task-breakdown",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/planning-and-task-breakdown/SKILL.md",
        required=True,
        phase="planning",
        purpose="Break specs into small verifiable TODOs with acceptance criteria and dependencies.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="incremental-implementation",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/incremental-implementation/SKILL.md",
        required=True,
        phase="implementation",
        purpose="Implement one thin vertical slice at a time with safe defaults.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="test-driven-development",
        provider="addyosmani/agent-skills or local installed skill",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/test-driven-development/SKILL.md",
        required=True,
        phase="validation",
        purpose="Use red-green-refactor and test evidence for each TODO.",
        install_hint="Use the already installed local test-driven-development skill, or inspect/install this linked SKILL.md.",
    ),
    ExternalSkill(
        name="debugging-and-error-recovery",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/debugging-and-error-recovery/SKILL.md",
        required=True,
        phase="debugging",
        purpose="Reproduce, localize, reduce, fix, and guard after validation failure.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="code-review-and-quality",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/code-review-and-quality/SKILL.md",
        required=True,
        phase="review",
        purpose="Run multi-axis review before accepting a TODO or merge.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="documentation-and-adrs",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/documentation-and-adrs/SKILL.md",
        required=True,
        phase="documentation",
        purpose="Document architecture decisions, APIs, behavior changes, and rationale.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="code-simplification",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md",
        required=False,
        phase="improvement",
        purpose="Preserve behavior while reducing complexity and maintenance cost.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="security-and-hardening",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/security-and-hardening/SKILL.md",
        required=False,
        phase="security-review",
        purpose="Review auth, user input, secrets, dependency, and data handling risks.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="performance-optimization",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/performance-optimization/SKILL.md",
        required=False,
        phase="performance-review",
        purpose="Run measure-first performance critique and improvement planning.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
    ExternalSkill(
        name="api-and-interface-design",
        provider="addyosmani/agent-skills",
        url="https://github.com/addyosmani/agent-skills/blob/main/skills/api-and-interface-design/SKILL.md",
        required=False,
        phase="interface-review",
        purpose="API boundary and interface critique.",
        install_hint="Install or reference this SKILL.md after inspection.",
    ),
]


def all_skills() -> List[ExternalSkill]:
    """Return every external skill entry."""

    return list(EXTERNAL_SKILLS)


def skills_for_phase(phase: str) -> List[ExternalSkill]:
    """Return skills associated with a phase."""

    return [skill for skill in EXTERNAL_SKILLS if skill.phase == phase]


def required_skills() -> List[ExternalSkill]:
    """Return skills marked required by the RDD workflow."""

    return [skill for skill in EXTERNAL_SKILLS if skill.required]


def find_skill(name: str) -> Optional[ExternalSkill]:
    """Find a skill entry by name, case-insensitive."""

    lowered = name.lower()
    for skill in EXTERNAL_SKILLS:
        if skill.name.lower() == lowered:
            return skill
    return None


def install_hints(names: Iterable[str]) -> List[str]:
    """Return install commands/hints for selected skill names."""

    hints: List[str] = []
    for name in names:
        skill = find_skill(name)
        if skill is None:
            hints.append(f"# Unknown skill: {name}")
            continue
        hints.append(f"# {skill.name}\n# {skill.url}\n{skill.install_hint}")
    return hints


def render_markdown(skills: Optional[Iterable[ExternalSkill]] = None) -> str:
    """Render skill entries as Markdown with explicit links and install hints."""

    entries = list(skills or EXTERNAL_SKILLS)
    lines = [
        "# External Skill Registry",
        "",
        "This file mirrors references/external-skills.md.",
        "Inspect third-party SKILL.md files before using their scripts or hooks.",
        "",
        f"- OpenAI Codex skills docs: {OPENAI_SKILLS_DOCS}",
        f"- OpenAI skills catalog: {OPENAI_SKILLS_REPO}",
        f"- Addy Osmani agent-skills catalog: {ADDY_AGENT_SKILLS_REPO}",
        "",
        "| Skill | Provider | Required | Phase | Link | Install/use hint | Purpose |",
        "|---|---|---:|---|---|---|---|",
    ]
    for skill in entries:
        required = "yes" if skill.required else "optional"
        lines.append(
            f"| `{skill.name}` | {skill.provider} | {required} | {skill.phase} | "
            f"{skill.url} | `{skill.install_hint}` | {skill.purpose} |"
        )
    return "\n".join(lines) + "\n"


def as_json(skills: Optional[Iterable[ExternalSkill]] = None) -> str:
    """Render skill entries as JSON."""

    return json.dumps([asdict(skill) for skill in (skills or EXTERNAL_SKILLS)], ensure_ascii=False, indent=2, sort_keys=True)


def write_registry(path: Path, *, markdown: bool = False) -> Path:
    """Write registry to a file as JSON or Markdown."""

    path.parent.mkdir(parents=True, exist_ok=True)
    content = render_markdown() if markdown else as_json() + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    """CLI entrypoint for external skill registry."""

    parser = argparse.ArgumentParser(description="Print review-driven-development external skill registry.")
    parser.add_argument("--phase")
    parser.add_argument("--required", action="store_true")
    parser.add_argument("--name", action="append", help="Specific skill name. Can be repeated.")
    parser.add_argument("--install-hints", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    if args.name:
        skills = [skill for name in args.name if (skill := find_skill(name)) is not None]
    elif args.required:
        skills = required_skills()
    elif args.phase:
        skills = skills_for_phase(args.phase)
    else:
        skills = all_skills()

    if args.write:
        print(write_registry(Path(args.write), markdown=args.markdown))
        return
    if args.install_hints:
        print("\n\n".join(install_hints(args.name or [skill.name for skill in skills])))
        return
    print(as_json(skills) if args.json else render_markdown(skills))


if __name__ == "__main__":
    main()
