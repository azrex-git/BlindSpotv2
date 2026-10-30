"""BlindSpot Agent Skills Package.

Standardized Agent Skills following the open specification (Linux Foundation / Anthropic / OpenAI).
"""

from blindspot.skills.activator import SkillActivator, SkillInjectionMode
from blindspot.skills.manager import (
    SkillMetadata,
    SkillValidationResult,
    get_bundled_skills_dir,
    install_skills_to_workspace,
    list_bundled_skills,
    parse_skill_file,
    validate_skill,
)
from blindspot.skills.registry import SkillRegistry, SkillSummary
from blindspot.skills.watcher import SkillWatcher

__all__ = [
    "SkillActivator",
    "SkillInjectionMode",
    "SkillMetadata",
    "SkillRegistry",
    "SkillSummary",
    "SkillValidationResult",
    "SkillWatcher",
    "get_bundled_skills_dir",
    "install_skills_to_workspace",
    "list_bundled_skills",
    "parse_skill_file",
    "validate_skill",
]
