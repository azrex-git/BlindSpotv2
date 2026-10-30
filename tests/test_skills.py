"""Tests for Agent Skills discovery, validation, installation, and CLI subcommands."""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from blindspot.cli import app
from blindspot.skills.manager import (
    get_bundled_skills_dir,
    install_skills_to_workspace,
    list_bundled_skills,
    parse_skill_file,
    validate_skill,
)

runner = CliRunner()


def test_bundled_skills_exist():
    """Verify all bundled skills are discoverable."""
    skills = list_bundled_skills()
    skill_names = {s.name for s in skills}
    expected = {
        "persona-elderly-user",
        "persona-tech-novice",
        "persona-motor-impaired",
        "persona-color-blind",
        "persona-light-sensitive",
    }
    assert expected.issubset(skill_names)


def test_bundled_skills_conform_to_spec():
    """Verify every bundled skill passes specification validation with 0 errors."""
    skills = list_bundled_skills()
    assert len(skills) >= 4

    for skill in skills:
        result = validate_skill(skill.skill_path)
        assert result.is_valid is True, f"Skill {result.name} failed validation: {result.errors}"
        assert len(result.errors) == 0
        assert skill.version == "1.0.0"
        assert len(skill.description) > 20
        # Progressive disclosure guideline: instructions within ~2500 tokens
        assert result.token_estimate < 2500


def test_validate_skill_detects_invalid_name(tmp_path: Path):
    """Verify validator catches illegal name formats and directory mismatches."""
    bad_dir = tmp_path / "Invalid_Name"
    bad_dir.mkdir()
    bad_file = bad_dir / "SKILL.md"
    bad_file.write_text(
        """---
name: Invalid_Name
description: Test skill with uppercase and underscore
metadata:
  version: "1.0.0"
---

# Title
## Output Format
Some format
## Rules
1. Rule one
2. Rule two
3. Rule three
""",
        encoding="utf-8",
    )

    result = validate_skill(bad_file)
    assert result.is_valid is False
    assert any("lowercase" in err.lower() for err in result.errors)


def test_validate_skill_detects_missing_sections(tmp_path: Path):
    """Verify validator flags missing Output Format or Rules sections."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        """---
name: test-skill
description: Minimal test skill lacking required structure
metadata:
  version: "1.0.0"
---

# Test Role
Just some text without output format or rules.
""",
        encoding="utf-8",
    )

    result = validate_skill(skill_file)
    assert result.is_valid is False
    assert any("output format" in err.lower() for err in result.errors)
    assert any("rules" in err.lower() for err in result.errors)


def test_install_skills_to_workspace(tmp_path: Path):
    """Verify skill installation exports to .agents/skills and .github/skills."""
    installed = install_skills_to_workspace(tmp_path, targets=["agents", "github"])

    assert "agents" in installed
    assert "github" in installed
    assert len(installed["agents"]) >= 4
    assert len(installed["github"]) >= 4

    for skill_file in installed["agents"]:
        assert skill_file.is_file()
        assert (tmp_path / ".agents" / "skills").is_dir()

    for skill_file in installed["github"]:
        assert skill_file.is_file()
        assert (tmp_path / ".github" / "skills").is_dir()


def test_cli_skill_list():
    """Verify 'blindspot skill list' outputs table of bundled skills."""
    result = runner.invoke(app, ["skill", "list"])
    assert result.exit_code == 0
    assert "persona-elderly-user" in result.output
    assert "persona-tech-novice" in result.output
    assert "persona-motor-impaired" in result.output
    assert "persona-color-blind" in result.output
    assert "persona-light-sensitive" in result.output


def test_cli_skill_validate():
    """Verify 'blindspot skill validate' validates all bundled skills."""
    result = runner.invoke(app, ["skill", "validate"])
    assert result.exit_code == 0
    assert "[PASS]" in result.output
    assert "persona-elderly-user" in result.output


def test_cli_skill_validate_invalid_path(tmp_path: Path):
    """Verify 'blindspot skill validate' on a missing path returns exit code 2."""
    missing = tmp_path / "nonexistent"
    result = runner.invoke(app, ["skill", "validate", str(missing)])
    assert result.exit_code == 2


def test_cli_skill_install(tmp_path: Path):
    """Verify 'blindspot skill install' exports to specified destination."""
    result = runner.invoke(app, ["skill", "install", "--dest", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "skills" / "persona-elderly-user" / "SKILL.md").is_file()
    assert (tmp_path / ".github" / "skills" / "persona-elderly-user" / "SKILL.md").is_file()


def test_skill_registry_progressive_disclosure():
    """Verify 3-tier progressive disclosure in SkillRegistry."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()
    summaries = reg.list_summaries()
    assert len(summaries) >= 5

    # Tier 1: summaries contain light metadata
    motor_sum = next(s for s in summaries if s.name == "persona-motor-impaired")
    assert "keyboard" in motor_sum.keywords
    assert motor_sum.version == "1.0.0"

    # Tier 2: Activation on demand with alias resolution
    motor_skill = reg.get_skill("motor")
    assert motor_skill is not None
    assert motor_skill.name == "persona-motor-impaired"
    assert "Keyboard" in motor_skill.body

    # Tier 2: Unknown skill returns None
    assert reg.get_skill("nonexistent-skill") is None


def test_skill_registry_slash_commands():
    """Verify slash command parsing for quick execution."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()

    skill, rest = reg.try_parse_slash_command("/elderly check font size")
    assert skill is not None
    assert skill.name == "persona-elderly-user"
    assert rest == "check font size"

    skill, rest = reg.try_parse_slash_command("/novice test form submission")
    assert skill is not None
    assert skill.name == "persona-tech-novice"
    assert rest == "test form submission"

    skill, rest = reg.try_parse_slash_command("regular user query without slash")
    assert skill is None
    assert rest == "regular user query without slash"


def test_skill_registry_find_matches():
    """Verify semantic keyword matching for incoming user intents."""
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()

    matches = reg.find_matches("keyboard focus switch tremors")
    assert len(matches) > 0
    assert matches[0][0].name == "persona-motor-impaired"

    color_matches = reg.find_matches("color blind deuteranopia contrast")
    assert len(color_matches) > 0
    assert color_matches[0][0].name == "persona-color-blind"


def test_skill_activator_injection_modes():
    """Verify prompt formatting across SkillInjectionMode."""
    from blindspot.skills.activator import SkillActivator, SkillInjectionMode
    from blindspot.skills.registry import SkillRegistry

    reg = SkillRegistry()
    activator = SkillActivator(reg)
    skill = reg.get_skill("elderly")
    assert skill is not None

    user_injection = activator.format_for_injection(
        skill, mode=SkillInjectionMode.USER_MESSAGE, user_request="Audit checkout page"
    )
    assert "ACTIVATED AGENT SKILL: persona-elderly-user" in user_injection
    assert "Audit checkout page" in user_injection

    sys_injection = activator.format_for_injection(
        skill, mode=SkillInjectionMode.SYSTEM_PROMPT
    )
    assert "[Active Specialized Skill: persona-elderly-user]" in sys_injection


def test_cli_skill_show_and_match():
    """Verify 'blindspot skill show' and 'blindspot skill match' CLI commands."""
    show_res = runner.invoke(app, ["skill", "show", "elderly"])
    assert show_res.exit_code == 0
    assert "persona-elderly-user" in show_res.output

    match_res = runner.invoke(app, ["skill", "match", "keyboard focus navigation"])
    assert match_res.exit_code == 0
    assert "persona-motor-impaired" in match_res.output


def test_mcp_skill_tools():
    """Verify MCP tools for Agent Skills discovery and retrieval."""
    from blindspot.mcp.tools import tool_get_skill, tool_list_skills

    list_res = tool_list_skills()
    assert list_res["skills_count"] >= 5
    skill_names = [s["name"] for s in list_res["skills"]]
    assert "persona-elderly-user" in skill_names
    assert "persona-motor-impaired" in skill_names

    get_res = tool_get_skill("elderly")
    assert get_res["name"] == "persona-elderly-user"
    assert "Arthur" in get_res["body"]

    bad_res = tool_get_skill("unknown-xyz")
    assert "error" in bad_res


def test_manual_markdown_persona_loader(tmp_path: Path):
    """Verify loading and parsing manual Markdown personas without generative AI overhead."""
    from blindspot.personas.generator import load_personas_from_markdown

    md_content = """# Persona Blueprint: Power User & Accessibility Specialist

### Persona 1: Sam - Screen Reader Specialist
- **Experience Level:** Expert
- **Device & Interaction:** NVDA + Desktop Chrome
- **Primary Goal:** Verify ARIA landmarks and keyboard accessibility.
- **Likely Difficulties:** Unlabelled icons, missing focus rings.
- **Accessibility Needs:** Screen Reader & High Contrast

#### Assigned Tasks:
1. **Verify Heading Structure**:
   - **Objective:** Navigate using H keys to ensure sequential H1 to H3 hierarchy.
   - **Starting Conditions:** Starts at top of page.
   - **Observable Success Criteria:** H1 element present, no skipped heading levels.
   - **Evidence to Collect:** Heading tag names, text content.

2. **Form Accessibility**:
   - **Objective:** Fill contact form with keyboard only.
   - **Starting Conditions:** Contact section.
   - **Observable Success Criteria:** Form submits successfully.
   - **Evidence to Collect:** Input labels, error messages.
"""
    plan = load_personas_from_markdown(md_content, website_url="https://example.com")
    assert len(plan.personas) == 1
    p = plan.personas[0]
    assert "Sam" in p.name
    assert p.experience_level == "Expert"
    assert len(p.tasks) == 2
    assert p.tasks[0].objective == "Navigate using H keys to ensure sequential H1 to H3 hierarchy."
    assert "H1 element present" in p.tasks[0].success_criteria[0]
    assert p.tasks[1].objective == "Fill contact form with keyboard only."


def test_build_agent_system_prompt_with_skill():
    """Verify build_agent_system_prompt dynamically injects active skill playbook."""
    from blindspot.execution.agent import build_agent_system_prompt

    # Default prompt includes safety guardrails
    base_prompt = build_agent_system_prompt()
    assert "PERCEPTION & INTERACTION" in base_prompt
    assert "CRITICAL SAFETY & INTEGRITY RULES" in base_prompt

    # Specialized elderly skill injection
    elderly_prompt = build_agent_system_prompt(skill="elderly")
    assert "PERCEPTION & INTERACTION" in elderly_prompt
    assert "persona-elderly-user" in elderly_prompt

    # Specialized motor skill injection
    motor_prompt = build_agent_system_prompt(skill="motor")
    assert "PERCEPTION & INTERACTION" in motor_prompt
    assert "persona-motor-impaired" in motor_prompt


def test_build_analysis_system_prompt_with_skill():
    """Verify build_analysis_system_prompt dynamically injects skill audit guidelines."""
    from blindspot.reporting.analysis import build_analysis_system_prompt

    base_prompt = build_analysis_system_prompt()
    assert "RULES FOR UX ANALYSIS" in base_prompt

    motor_prompt = build_analysis_system_prompt(skill="motor")
    assert "RULES FOR UX ANALYSIS" in motor_prompt
    assert "persona-motor-impaired" in motor_prompt

