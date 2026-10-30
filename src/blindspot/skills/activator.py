"""Agent Skill Activator: formats and injects skill playbooks into AI conversations.

Following the open Agent Skills specification, this module converts a SkillMetadata definition
into structured prompt injections to enforce output formatting, operational checklists, and rules.
"""

from enum import Enum
from typing import Optional

from blindspot.skills.manager import SkillMetadata
from blindspot.skills.registry import SkillRegistry


class SkillInjectionMode(str, Enum):
    """Modes for injecting skill instructions into the AI provider context."""

    USER_MESSAGE = "user_message"
    SYSTEM_PROMPT = "system_prompt"
    TOOL_RESULT = "tool_result"


class SkillActivator:
    """Formats and injects active skill playbooks into model prompts."""

    def __init__(self, registry: Optional[SkillRegistry] = None) -> None:
        self.registry = registry or SkillRegistry()

    def format_for_injection(
        self,
        skill: SkillMetadata,
        mode: SkillInjectionMode = SkillInjectionMode.USER_MESSAGE,
        user_request: Optional[str] = None,
    ) -> str:
        """Format a skill's full playbook into an explicit prompt injection."""
        header = (
            f"=== ACTIVATED AGENT SKILL: {skill.name} (v{skill.version}) ===\n"
            f"Description: {skill.description}\n"
        )
        if skill.allowed_tools:
            header += f"Approved Tools: {skill.allowed_tools}\n"
        header += "========================================================\n\n"

        body = skill.body.strip()

        combined = f"{header}{body}\n\n========================================================"

        if mode == SkillInjectionMode.USER_MESSAGE:
            if user_request:
                return f"{combined}\n\nUser Context / Task Objective:\n{user_request}"
            return combined

        elif mode == SkillInjectionMode.SYSTEM_PROMPT:
            return f"\n\n[Active Specialized Skill: {skill.name}]\n{body}"

        elif mode == SkillInjectionMode.TOOL_RESULT:
            return f"Skill '{skill.name}' successfully activated.\nInstructions:\n{body}"

        return combined

    def build_system_instructions(self, skill: SkillMetadata) -> str:
        """Generate focused system-level guidelines from a skill's rules and output format."""
        return self.format_for_injection(skill, mode=SkillInjectionMode.SYSTEM_PROMPT)
