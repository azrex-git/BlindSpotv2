"""Browser-Use integration for BlindSpot autonomous persona execution.

Seamlessly bridges BlindSpot Persona blueprints and tasks into browser_use.Agent,
providing state-of-the-art vision-and-coordinate browser automation, tab management,
and resilient DOM interaction.
"""

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Optional, Union

from blindspot.ai.base import BaseAIProvider
from blindspot.execution.models import (
    ActionExecutionRecord,
    ActionType,
    AgentAction,
    ExecutionRunResult,
    PersonaExecutionResult,
    TaskExecutionResult,
    TaskStatus,
)
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask

logger = logging.getLogger(__name__)


def is_browser_use_available() -> bool:
    """Check if the browser-use package is installed and importable."""
    try:
        import browser_use
        return True
    except ImportError:
        import sys
        # Check if local browser-use repository exists in project root
        candidate = Path(__file__).resolve().parent.parent.parent.parent / "browser-use"
        if candidate.is_dir() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            try:
                import browser_use
                return True
            except ImportError:
                pass
        return False


def build_persona_system_extension(persona: Persona, skill: Optional[str] = None) -> str:
    """Construct persona behavioral guidance and constraints for browser-use Agent."""
    directives = [
        f"You are simulating a realistic user named '{persona.name}'.",
        f"Background / Context: {persona.description}",
        f"Experience Level: {persona.experience_level}",
        f"Assistive Devices / Needs: {persona.accessibility_needs or 'Standard browsing'}",
    ]
    role = getattr(persona, "role", None)
    if role:
        directives.insert(1, f"Role / Archetype: {role}")


    difficulties = getattr(persona, "likely_difficulties", None) or getattr(persona, "friction_expectations", None)
    if difficulties:
        directives.append("Anticipated Usability Friction Points:")
        for item in difficulties:
            directives.append(f" - {item}")

    directives.extend([
        "\nEXECUTION GUIDELINES:",
        "1. Complete the stated user task as this persona would realistically behave.",
        "2. Note any confusing UX, broken buttons, missing accessibility labels, or layout shift.",
        "3. Once the goal is completed, call the done action with an assessment of whether the user achieved their intent.",
        "4. NEVER enter real personal passwords, payment cards, or delete critical live data.",
    ])

    if skill:
        try:
            from blindspot.skills.registry import SkillRegistry
            reg = SkillRegistry()
            sk = reg.get_skill(skill)
            if sk and sk.body:
                directives.append(f"\nSPECIALIZED AUDIT DIRECTIVES ({sk.name}):\n{sk.body}")
        except Exception as e:
            logger.debug(f"Could not load skill directives: {e}")

    return "\n".join(directives)


def resolve_browser_use_llm(provider: Optional[BaseAIProvider] = None):
    """Translate BlindSpot BaseAIProvider or environment configuration into a browser_use chat model."""
    # The native provider talks to the IDE bridge and local heuristics; it is
    # not an OpenAI-compatible endpoint and must never be silently mapped to a
    # hosted model by browser-use.
    if provider is not None and getattr(provider, "name", "").lower() == "antigravity":
        return None

    try:
        from browser_use.llm.litellm.chat import ChatLiteLLM
    except ImportError:
        return None

    model_name = getattr(provider, "model", None) or getattr(provider, "_model", None)
    if not model_name:
        import os
        model_name = os.environ.get("BLINDSPOT_LLM") or os.environ.get("LLM_MODEL")

    if not model_name:
        return None

    api_key = getattr(provider, "_api_key", None)
    api_base = getattr(provider, "base_url", None) or getattr(provider, "_base_url", None)

    return ChatLiteLLM(
        model=model_name,
        api_key=api_key,
        api_base=api_base or None,
    )


class BrowserUseTaskAgent:
    """Executes persona tasks using browser-use Agent."""

    def __init__(
        self,
        provider: Optional[BaseAIProvider] = None,
        max_actions: int = 15,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        skill: Optional[str] = None,
        llm: Optional[Any] = None,
    ) -> None:
        self.provider = provider
        self.max_actions = max_actions
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.skill = skill
        self.llm = llm or resolve_browser_use_llm(provider)
        if self.llm is None:
            raise RuntimeError(
                "The browser-use engine needs a compatible configured model. "
                "Use the native engine for Antigravity, or configure a local or hosted model explicitly."
            )

    def execute_task(
        self,
        persona: Persona,
        task: PersonaTask,
        target_url: str,
        evidence_dir: Path,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> TaskExecutionResult:
        """Run a single persona task through browser-use Agent and capture results."""
        from browser_use import Agent, BrowserProfile, BrowserSession

        evidence_dir.mkdir(parents=True, exist_ok=True)
        start_time = datetime.now(timezone.utc).isoformat()
        actions_taken: List[ActionExecutionRecord] = []
        evidence_screenshots: List[str] = []

        system_extension = build_persona_system_extension(persona, self.skill)

        crit = ", ".join(task.success_criteria) if isinstance(task.success_criteria, list) else str(task.success_criteria)
        full_task_prompt = (
            f"Navigate to {target_url}\n"
            f"Persona Goal: {task.objective}\n"
            f"Success Criteria: {crit}\n"
            f"Please complete this goal step-by-step and call done when finished."
        )

        profile = BrowserProfile(
            headless=self.headless,
            viewport={"width": self.viewport_width, "height": self.viewport_height},
        )
        browser = BrowserSession(browser_profile=profile)

        step_counter = 0

        def _step_callback(state_summary, agent_output, step_num):
            nonlocal step_counter
            step_counter = step_num
            if on_event:
                try:
                    thinking = getattr(agent_output, "thinking", "") or ""
                    on_event({
                        "type": "task_step",
                        "persona_id": persona.id,
                        "persona_name": persona.name,
                        "task_id": task.id,
                        "step": step_num,
                        "thinking": thinking,
                        "url": getattr(state_summary, "url", target_url),
                    })
                except Exception:
                    pass

        agent = Agent(
            task=full_task_prompt,
            llm=self.llm,
            browser=browser,
            extend_system_message=system_extension,
            max_actions_per_step=3,
            use_vision=True,
            directly_open_url=True,
            register_new_step_callback=_step_callback,
        )

        final_url = target_url
        final_status = TaskStatus.INCONCLUSIVE
        error_message: Optional[str] = None
        notes: Optional[str] = None

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with ThreadPoolExecutor(max_workers=1) as executor:
                    history = executor.submit(agent.run_sync, max_steps=self.max_actions).result()
            else:
                history = agent.run_sync(max_steps=self.max_actions)

            # Process history items into BlindSpot ActionExecutionRecord objects
            for idx, item in enumerate(history.history, start=1):
                step_url = getattr(item.state, "url", final_url) or final_url
                step_title = getattr(item.state, "title", "Unknown") or "Unknown"
                final_url = step_url

                # Save screenshot if present in state
                screenshot_rel: Optional[str] = None
                raw_screenshot = getattr(item.state, "screenshot", None)
                if raw_screenshot:
                    shot_filename = f"{task.id}_step{idx}.png"
                    shot_path = evidence_dir / shot_filename
                    try:
                        img_bytes = base64.b64decode(raw_screenshot)
                        with open(shot_path, "wb") as f:
                            f.write(img_bytes)
                        screenshot_rel = f"evidence/{shot_filename}"
                        evidence_screenshots.append(str(shot_path))
                    except Exception as e:
                        logger.debug(f"Failed to decode step screenshot: {e}")

                # Extract actions and reasoning
                model_out = getattr(item, "model_output", None)
                thinking = getattr(model_out, "thinking", "") or ""
                next_goal = getattr(model_out, "next_goal", "") or ""
                reasoning = thinking or next_goal or f"Executing step {idx}"

                actions = getattr(model_out, "action", []) or []
                action_name = "unknown"
                target_desc = "page"
                text_val = None

                if actions:
                    act = actions[0]
                    act_dump = act.model_dump(exclude_none=True) if hasattr(act, "model_dump") else act
                    if isinstance(act_dump, dict):
                        for k, v in act_dump.items():
                            action_name = k
                            if isinstance(v, dict):
                                target_desc = str(v.get("index") or v.get("coordinate") or v.get("url") or "element")
                                text_val = v.get("text")
                            break

                mapped_type = ActionType.CLICK
                if "click" in action_name:
                    mapped_type = ActionType.CLICK
                elif "input" in action_name or "fill" in action_name or "type" in action_name:
                    mapped_type = ActionType.FILL
                elif "scroll" in action_name:
                    mapped_type = ActionType.SCROLL
                elif "navigate" in action_name or "go_to" in action_name:
                    mapped_type = ActionType.NAVIGATE
                elif "done" in action_name:
                    mapped_type = ActionType.FINISH
                elif "wait" in action_name:
                    mapped_type = ActionType.WAIT

                # Action success
                step_success = True
                results = getattr(item, "result", []) or []
                if results and hasattr(results[0], "error") and results[0].error:
                    step_success = False

                agent_action = AgentAction(
                    action=mapped_type,
                    target=target_desc,
                    text=text_val,
                    value=text_val,
                    reasoning=reasoning,
                )

                record = ActionExecutionRecord(
                    step=idx,
                    action=agent_action,
                    success=step_success,
                    page_url=step_url,
                    page_title=step_title,
                    screenshot_path=screenshot_rel,
                )
                actions_taken.append(record)

            # Determine task completion status
            is_done = False
            for item in history.history:
                results = getattr(item, "result", []) or []
                for res in results:
                    if getattr(res, "is_done", False):
                        is_done = True
                        notes = getattr(res, "extracted_content", None) or "Task completed successfully."
                        break
                if is_done:
                    break

            if is_done:
                final_status = TaskStatus.SUCCESS
            elif len(history.history) >= self.max_actions:
                final_status = TaskStatus.FAILURE
                error_message = f"Reached maximum action limit ({self.max_actions}) without meeting success criteria."
            else:
                final_status = TaskStatus.INCONCLUSIVE

        except Exception as exc:
            logger.error(f"Error during browser-use execution for task {task.id}: {exc}", exc_info=True)
            final_status = TaskStatus.FAILURE
            error_message = str(exc)
        finally:
            # Clean up browser session
            try:
                if loop and loop.is_running():
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        executor.submit(asyncio.run, browser.stop()).result()
                else:
                    asyncio.run(browser.stop())
            except Exception:
                pass

        end_time = datetime.now(timezone.utc).isoformat()

        return TaskExecutionResult(
            task_id=task.id,
            persona_id=persona.id,
            task_objective=task.objective,
            status=final_status,
            start_time=start_time,
            end_time=end_time,
            initial_url=target_url,
            final_url=final_url,
            actions_taken=actions_taken,
            evidence_screenshots=evidence_screenshots,
            notes=notes,
            error_message=error_message,
        )


class BrowserUsePersonaRunner:
    """Orchestrates plan execution across all personas using browser-use agents."""

    def __init__(
        self,
        provider: Optional[BaseAIProvider] = None,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 800,
        max_actions_per_task: int = 15,
        skill: Optional[str] = None,
        max_personas: Optional[int] = None,
    ) -> None:
        self.provider = provider
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.max_actions_per_task = max_actions_per_task
        self.skill = skill
        self.max_personas = max_personas

    def run_plan(
        self,
        plan: PersonaPlan,
        output_dir: Union[str, Path],
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> ExecutionRunResult:
        """Run all personas and tasks using browser-use agents."""
        run_dir = Path(output_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

        personas_to_run = plan.personas
        if self.max_personas and self.max_personas > 0:
            personas_to_run = personas_to_run[: self.max_personas]

        start_time = datetime.now(timezone.utc).isoformat()
        persona_results: List[PersonaExecutionResult] = []

        for persona in personas_to_run:
            if cancel_check and cancel_check():
                break

            persona_evidence_dir = run_dir / "personas" / persona.id / "evidence"
            persona_evidence_dir.mkdir(parents=True, exist_ok=True)

            agent = BrowserUseTaskAgent(
                provider=self.provider,
                max_actions=self.max_actions_per_task,
                headless=self.headless,
                viewport_width=self.viewport_width,
                viewport_height=self.viewport_height,
                skill=self.skill,
            )

            task_results: List[TaskExecutionResult] = []
            for task in persona.tasks:
                if cancel_check and cancel_check():
                    break

                task_evidence_dir = persona_evidence_dir / task.id
                task_res = agent.execute_task(
                    persona=persona,
                    task=task,
                    target_url=plan.website_url,
                    evidence_dir=task_evidence_dir,
                    on_event=on_event,
                )
                task_results.append(task_res)

            p_result = PersonaExecutionResult(
                persona_id=persona.id,
                persona_name=persona.name,
                task_results=task_results,
            )
            persona_results.append(p_result)

        end_time = datetime.now(timezone.utc).isoformat()

        # Compute summary metrics
        total = sum(len(p.task_results) for p in persona_results)
        passed = sum(1 for p in persona_results for t in p.task_results if t.status == TaskStatus.SUCCESS)
        failed = sum(1 for p in persona_results for t in p.task_results if t.status == TaskStatus.FAILURE)
        inconclusive = total - passed - failed

        exec_res = ExecutionRunResult(
            target_url=plan.website_url,
            browser="browser-use",
            headless=self.headless,
            personas=persona_results,
            results_file_path=str(run_dir / "execution_results.json"),
        )

        # Save execution results JSON
        with open(run_dir / "execution_results.json", "w", encoding="utf-8") as f:
            json.dump(exec_res.model_dump(), f, indent=2)

        return exec_res
