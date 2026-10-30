"""Renderer for full autonomous persona interaction logs in Markdown.

Captures the visual persona journey: step-by-step persona thoughts, screenshots
analyzed before each action, dispatched actions, target element attributes,
resulting state screenshots, and final outcome evidence without verbose raw HTML dumps.
"""

from pathlib import Path
from typing import Dict, List, Optional
from blindspot.execution.models import (
    ActionExecutionRecord,
    ExecutionRunResult,
    PersonaExecutionResult,
    TaskExecutionResult,
)
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask


def render_task_interaction_markdown(
    persona: Persona,
    task: PersonaTask,
    task_result: TaskExecutionResult,
    output_dir: Optional[Path] = None,
) -> str:
    """Render a clean Markdown log of a single persona task interaction with visual screenshots."""
    lines: List[str] = []

    lines.append(f"## 👤 Persona: {persona.name} ({getattr(persona, 'experience_level', 'Standard')})")
    lines.append(f"> {persona.description}")
    lines.append("")
    lines.append(f"### 🎯 Task: {task.objective}")
    lines.append(f"- **Task ID**: `{task.id}`")
    lines.append(f"- **Task Status**: `{task_result.status.value.upper()}`")
    lines.append(f"- **Initial URL**: `{task_result.initial_url}`")
    lines.append(f"- **Final URL**: `{task_result.final_url}`")
    lines.append(f"- **Started**: `{task_result.start_time}`")
    lines.append(f"- **Finished**: `{task_result.end_time}`")
    lines.append("")

    # Success criteria
    criteria_list = task.success_criteria if isinstance(task.success_criteria, list) else [str(task.success_criteria)]
    lines.append("#### 🎯 Observable Success Criteria")
    for crit in criteria_list:
        lines.append(f"- {crit}")
    lines.append("")

    # Initial baseline screenshot for task if available
    if task_result.actions_taken and task_result.actions_taken[0].screenshot_path:
        first_shot = task_result.actions_taken[0].screenshot_path
        rel_first = first_shot
        if output_dir:
            try:
                rel_first = str(Path(first_shot).relative_to(output_dir)).replace("\\", "/")
            except Exception:
                pass
        lines.append(f"![Initial Page State Before Actions]({rel_first})")
        lines.append("")

    # Step-by-Step Action History with Screenshots
    lines.append("---")
    lines.append("### 👣 Step-by-Step Persona Visual Journey & Actions")
    lines.append("")

    if not task_result.actions_taken:
        lines.append("*No action steps were executed for this task.*")
        lines.append("")
    else:
        for rec in task_result.actions_taken:
            act = rec.action
            act_type = act.action.value.upper() if hasattr(act.action, "value") else str(act.action).upper()
            target_desc = act.target or (f"@{act.mark}" if act.mark is not None else "")
            header_target = f" → `{target_desc}`" if target_desc else ""

            status_badge = "✓ SUCCESS" if rec.success else "✖ FAILED"
            lines.append(f"#### Step {rec.step}: `{act_type}`{header_target} ({status_badge})")
            lines.append("")
            lines.append(f"- **Page URL**: `{rec.page_url}`")
            lines.append(f"- **Page Title**: {rec.page_title}")
            if act.reasoning:
                lines.append(f"- **Persona Observation & Decision**: *\"{act.reasoning}\"*")

            # Action attributes
            val = act.value or act.text or ""
            if val:
                lines.append(f"- **Input Text**: `{val}`")
            if act.key:
                lines.append(f"- **Key Pressed**: `{act.key}`")
            if act.direction:
                lines.append(f"- **Scroll Direction**: `{act.direction}` ({act.amount}px)")

            # Target element metadata
            if rec.target_element:
                el = rec.target_element
                lines.append("- **Target Control Details**:")
                lines.append(f"  - **Tag**: `<{el.get('tag', 'unknown')}>`")
                lines.append(f"  - **Ref**: `{el.get('ref', target_desc)}`")
                if el.get("text"):
                    lines.append(f"  - **Visible Text**: \"{el['text']}\"")
                if el.get("aria_label"):
                    lines.append(f"  - **Accessible Label**: \"{el['aria_label']}\"")
                if el.get("id"):
                    lines.append(f"  - **ID**: `#{el['id']}`")

            if rec.error:
                lines.append(f"- **Action Error**: `{rec.error}`")

            # Screenshot image embed
            if rec.screenshot_path:
                rel_path = rec.screenshot_path
                if output_dir:
                    try:
                        rel_path = str(Path(rec.screenshot_path).relative_to(output_dir)).replace("\\", "/")
                    except Exception:
                        pass
                lines.append("")
                lines.append(f"![Step {rec.step} Screenshot]({rel_path})")
                lines.append("")

    # Task Outcome & Evidence
    lines.append("---")
    lines.append("#### 🏆 Task Outcome & Verified Evidence")
    lines.append("")
    lines.append(f"- **Final Status**: `{task_result.status.value.upper()}`")
    if task_result.error_message:
        lines.append(f"- **Failure / Inconclusive Reason**: {task_result.error_message}")
    if task_result.notes:
        lines.append(f"- **Persona Observation Notes**: {task_result.notes}")

    if task_result.evidence:
        lines.append("##### 🔎 Verified Evidence Items")
        for ev in task_result.evidence:
            lines.append(f"- {ev}")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def render_full_run_interaction_markdown(
    plan: Optional[PersonaPlan],
    execution_result: Optional[ExecutionRunResult],
    output_dir: Path,
    inspection_result: Optional[Any] = None,
) -> str:
    """Render a unified Markdown log for browser interaction and visual persona journeys."""
    lines: List[str] = []

    target_url = (
        (execution_result.target_url if execution_result else None)
        or (inspection_result.final_url if inspection_result else None)
        or (inspection_result.requested_url if inspection_result else None)
        or "Target Website"
    )
    lines.append("# 🧭 BlindSpot Browser Interaction Log")
    lines.append("")
    lines.append(f"- **Target Website**: [{target_url}]({target_url})")
    gen_time = (
        (getattr(execution_result, "timestamp", None) if execution_result else None)
        or (getattr(inspection_result, "timestamp", None) if inspection_result else None)
        or "N/A"
    )
    lines.append(f"- **Timestamp**: `{gen_time}`")
    lines.append("- **Browser Automation**: Playwright Headed / Visible Desktop")
    lines.append("- **Inspection Mode**: Screenshot-Driven Visual Analysis (DOM code dumps disabled)")
    lines.append("")

    # Initial website baseline
    if inspection_result:
        lines.append("## 📸 Initial Website Baseline & Screenshot")
        lines.append("")
        lines.append(f"- **Page Title**: `{getattr(inspection_result, 'title', 'Unknown')}`")
        lines.append(f"- **Final URL**: `{getattr(inspection_result, 'final_url', target_url)}`")
        vp = getattr(inspection_result, "viewport", None)
        if vp:
            lines.append(f"- **Viewport**: `{vp.width}x{vp.height}`")
        summ = getattr(inspection_result, "summary", None)
        if summ:
            lines.append(f"- **Interactive Elements Detected**: {summ.total_interactive_elements} (Links: {summ.links_count}, Buttons: {summ.buttons_count}, Inputs: {summ.form_fields_count})")
        lines.append("")

        # Baseline screenshot
        screenshot_path = getattr(inspection_result, "screenshot_path", None)
        if screenshot_path:
            rel_shot = screenshot_path
            try:
                rel_shot = str(Path(screenshot_path).relative_to(output_dir)).replace("\\", "/")
            except Exception:
                pass
            lines.append(f"![Initial Website Screenshot]({rel_shot})")
            lines.append("")

    if not execution_result:
        lines.append("*Initial visual inspection completed. No persona execution was run.*")
        return "\n".join(lines)

    personas = getattr(execution_result, "personas", None) or getattr(execution_result, "persona_results", [])
    lines.append(f"## 📊 Persona Journey Execution: {len(personas)} Personas Tested")
    lines.append("")

    plan_persona_map: Dict[str, Persona] = {}
    if plan and plan.personas:
        plan_persona_map = {p.id: p for p in plan.personas}

    for p_idx, p_res in enumerate(personas, start=1):
        p_obj = plan_persona_map.get(p_res.persona_id)
        p_name = getattr(p_res, "persona_name", getattr(p_obj, "name", f"Persona {p_idx}"))
        p_exp = getattr(p_obj, "experience_level", "Standard") if p_obj else "Standard"

        lines.append("---")
        tasks = getattr(p_res, "tasks", None) or getattr(p_res, "task_results", [])
        for t_idx, t_res in enumerate(tasks, start=1):
            t_obj = None
            if p_obj and p_obj.tasks:
                for cand in p_obj.tasks:
                    if cand.id == t_res.task_id:
                        t_obj = cand
                        break
            if not t_obj:
                t_obj = PersonaTask(
                    id=t_res.task_id,
                    objective=t_res.task_objective,
                    success_criteria=["Complete user journey"],
                )

            task_md = render_task_interaction_markdown(
                persona=p_obj or Persona(id=p_res.persona_id, name=p_name, description=p_name, experience_level=p_exp),
                task=t_obj,
                task_result=t_res,
                output_dir=output_dir,
            )
            lines.append(task_md)
            lines.append("")

    return "\n".join(lines)
