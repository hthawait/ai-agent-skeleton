"""
config.py
---------
Single-agent MVP. All business logic — prompt, persona, rules, skills,
tool descriptions — lives in .md files. This module's only job is to
load that markdown into a config object. No business logic belongs
here.

Layout:
    instructions/system_prompt.md
    instructions/persona.md
    instructions/rules.md
    instructions/skills/*.md   <- one file per skill (a capability the
                                  agent knows how to do — e.g. how to
                                  handle a refund request, how to write
                                  a summary in the house style)
    tools/*.md                  <- one file per tool, its description
                                  for the LLM (what it does / when to
                                  call it)
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field

ROOT_DIR = Path(__file__).resolve().parent.parent
INSTRUCTIONS_DIR = ROOT_DIR / "instructions"
SKILLS_DIR = INSTRUCTIONS_DIR / "skills"
TOOLS_DIR = ROOT_DIR / "tools"


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _read_all_md(directory: Path) -> dict[str, str]:
    """Read every .md file in a directory into {stem: content}."""
    if not directory.exists():
        return {}
    return {p.stem: _read(p) for p in sorted(directory.glob("*.md"))}


@dataclass
class AgentConfig:
    """Everything the agent needs, assembled from markdown files."""

    system_prompt: str = ""
    persona: str = ""
    rules: str = ""
    skills: dict[str, str] = field(default_factory=dict)
    tool_docs: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "AgentConfig":
        return cls(
            system_prompt=_read(INSTRUCTIONS_DIR / "system_prompt.md"),
            persona=_read(INSTRUCTIONS_DIR / "persona.md"),
            rules=_read(INSTRUCTIONS_DIR / "rules.md"),
            skills=_read_all_md(SKILLS_DIR),
            tool_docs=_read_all_md(TOOLS_DIR),
        )

    def build_system_prompt(self) -> str:
        """Concatenate prompt + persona + rules + all skills into one
        system prompt. MVP approach: every skill is always included.
        (If skills grow numerous or you want to save tokens, swap this
        for a step that picks relevant skills per request instead of
        loading all of them — but that selection logic is itself
        business logic, so keep the *criteria* in markdown too, e.g. a
        skills/README.md index the model or a router reads first.)
        """
        parts = [self.system_prompt, self.persona, self.rules]
        if self.skills:
            skills_section = "\n\n".join(
                f"### Skill: {name}\n{text}" for name, text in self.skills.items()
            )
            parts.append(f"## Skills\n\n{skills_section}")
        return "\n\n---\n\n".join(p for p in parts if p)
