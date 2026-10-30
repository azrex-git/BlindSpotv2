"""Step-gate task tracker for autonomous persona execution.

Enforces strict sequential progression across milestone steps:
The AI is strictly prohibited from executing Step N+1 until Step N has verified PASS criteria.
Maintains and updates task_tracker.md in real time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from blindspot.personas.models import PersonaTask


class MilestoneStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_USER = "WAITING_USER"
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class MilestoneStep:
    """An individual gated milestone step within a persona journey."""

    step_num: int
    title: str
    objective: str
    preconditions: str
    verification_gate: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    evidence: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def status_badge(self) -> str:
        if self.status == MilestoneStatus.PASSED:
            return "✅ PASSED"
        elif self.status == MilestoneStatus.IN_PROGRESS:
            return "🔵 IN_PROGRESS"
        elif self.status == MilestoneStatus.WAITING_USER:
            return "🟡 WAITING_USER"
        elif self.status == MilestoneStatus.FAILED:
            return "❌ FAILED"
        return "⏳ PENDING"


class TaskTracker:
    """Manages milestone decomposition, step-gating enforcement, and live task_tracker.md persistence."""

    def __init__(
        self,
        target_url: str,
        objective: str,
        tracker_path: Optional[Path] = None,
        unlimited: bool = True,
    ) -> None:
        self.target_url = target_url
        self.objective = objective
        self.tracker_path = tracker_path
        self.unlimited = unlimited
        self.milestones: List[MilestoneStep] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.created_at

    def decompose_task(self, task: PersonaTask, initial_url: str) -> List[MilestoneStep]:
        """Decompose a persona task into ordered, gated milestones with verification criteria."""
        obj_lower = task.objective.lower()
        milestones: List[MilestoneStep] = []

        # 1. Discovery / Navigation milestone
        is_search = any(k in obj_lower for k in ("search", "find", "locate", "query", "explore"))
        if is_search:
            milestones.append(
                MilestoneStep(
                    step_num=1,
                    title="Discovery & Search Query",
                    objective=f"Locate search input and submit targeted search query for task: {task.objective[:60]}",
                    preconditions=f"Website accessible at {initial_url}",
                    verification_gate="Search results page loaded with relevant query listings",
                    status=MilestoneStatus.PENDING,
                )
            )
        else:
            milestones.append(
                MilestoneStep(
                    step_num=1,
                    title="Website Navigation & Orientation",
                    objective=f"Navigate to entry point and orient controls for: {task.objective[:60]}",
                    preconditions=f"Website accessible at {initial_url}",
                    verification_gate="Target landing page DOM loaded with primary navigation controls",
                    status=MilestoneStatus.PENDING,
                )
            )

        # 2. Entity Selection / Exploration milestone
        has_product = any(k in obj_lower for k in ("product", "item", "iphone", "laptop", "result", "listing", "details"))
        if has_product:
            milestones.append(
                MilestoneStep(
                    step_num=2,
                    title="Target Entity Selection",
                    objective="Select in-stock product listing and open dedicated details page",
                    preconditions="Step 1 PASSED (Search results / catalog loaded)",
                    verification_gate="Product details page (PDP) loaded with specifications and pricing",
                    status=MilestoneStatus.PENDING,
                )
            )

        # Authentication is handled only when a real login/OTP barrier is detected.
        # Do not add an unconditional auth gate to ordinary browsing and form tasks.

        # 3. Conversion / Core Action milestone
        has_cart = any(k in obj_lower for k in ("cart", "buy", "purchase", "checkout", "bag", "order"))
        if has_cart:
            milestones.append(
                MilestoneStep(
                    step_num=len(milestones) + 1,
                    title="Trigger Conversion Action",
                    objective="Trigger primary 'Add to Cart' or 'Buy Now' action with chosen options",
                    preconditions=f"Step {len(milestones)} PASSED (Unobstructed product page)",
                    verification_gate="Add-to-cart confirmation received or cart drawer opened",
                    status=MilestoneStatus.PENDING,
                )
            )
            milestones.append(
                MilestoneStep(
                    step_num=len(milestones) + 1,
                    title="Cart & Funnel Verification",
                    objective="Navigate to shopping cart page, verify item presence, and locate checkout button",
                    preconditions=f"Step {len(milestones)} PASSED (Item added to cart)",
                    verification_gate="Cart URL (/cart or /viewcart) verified with item total and checkout action",
                    status=MilestoneStatus.PENDING,
                )
            )
        else:
            milestones.append(
                MilestoneStep(
                    step_num=len(milestones) + 1,
                    title="Execute Core Persona Journey Action",
                    objective=task.objective,
                    preconditions=f"Step {len(milestones)} PASSED",
                    verification_gate="Explicit observable success criteria verified on page",
                    status=MilestoneStatus.PENDING,
                )
            )

        self.milestones = milestones
        if self.milestones:
            self.milestones[0].status = MilestoneStatus.IN_PROGRESS
            self.milestones[0].started_at = datetime.now(timezone.utc).isoformat()

        self.persist()
        return self.milestones

    def get_active_milestone(self) -> Optional[MilestoneStep]:
        """Return the current active milestone that must be satisfied.
        
        Step-Gate Rule: Returns the first milestone that is NOT PASSED.
        Milestones after this step are strictly LOCKED.
        """
        for m in self.milestones:
            if m.status != MilestoneStatus.PASSED:
                if m.status == MilestoneStatus.PENDING:
                    m.status = MilestoneStatus.IN_PROGRESS
                    m.started_at = datetime.now(timezone.utc).isoformat()
                    self.persist()
                return m
        return None

    def mark_milestone_passed(self, step_num: int, evidence: str) -> None:
        """Mark a milestone as PASSED, unlock the next milestone, and update tracker."""
        for idx, m in enumerate(self.milestones):
            if m.step_num == step_num:
                m.status = MilestoneStatus.PASSED
                m.evidence = evidence
                m.completed_at = datetime.now(timezone.utc).isoformat()
                # Unlock next milestone
                if idx + 1 < len(self.milestones):
                    next_m = self.milestones[idx + 1]
                    if next_m.status == MilestoneStatus.PENDING:
                        next_m.status = MilestoneStatus.IN_PROGRESS
                        next_m.started_at = datetime.now(timezone.utc).isoformat()
                break
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.persist()

    def mark_milestone_waiting_user(self, step_num: int, reason: str) -> None:
        """Mark milestone as WAITING_USER (e.g. awaiting OTP or Email)."""
        for m in self.milestones:
            if m.step_num == step_num:
                m.status = MilestoneStatus.WAITING_USER
                m.evidence = f"Awaiting user input: {reason}"
                break
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.persist()

    def mark_milestone_failed(self, step_num: int, error: str) -> None:
        """Mark milestone as FAILED."""
        for m in self.milestones:
            if m.step_num == step_num:
                m.status = MilestoneStatus.FAILED
                m.error = error
                break
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.persist()

    def all_milestones_passed(self) -> bool:
        """Return True only if every defined milestone has attained PASSED status."""
        return bool(self.milestones) and all(m.status == MilestoneStatus.PASSED for m in self.milestones)

    def render_markdown(self) -> str:
        """Render the complete task_tracker.md markdown document."""
        lines: List[str] = []
        lines.append("# 📋 Autonomous Persona Task Tracker")
        lines.append("")
        lines.append(f"- **Target Website**: [{self.target_url}]({self.target_url})")
        lines.append(f"- **Journey Objective**: {self.objective}")
        lines.append(f"- **Gating Strategy**: Strict Precondition Gate (Step N+1 unlocked only after Step N is PASSED)")
        budget_str = "Unlimited (Autonomous completion loop)" if self.unlimited else "Capped"
        lines.append(f"- **Action Budget**: {budget_str}")
        lines.append(f"- **Started**: `{self.created_at}`")
        lines.append(f"- **Last Updated**: `{self.last_updated}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🚦 Milestone Execution Matrix")
        lines.append("")
        lines.append("| Step | Milestone Task | Preconditions | Gate Status | Verification Gate | Evidence Collected |")
        lines.append("| :---: | :--- | :--- | :---: | :--- | :--- |")

        for m in self.milestones:
            ev_display = m.evidence or (f"⚠️ {m.error}" if m.error else "Pending")
            lines.append(
                f"| **{m.step_num}** | {m.title} | {m.preconditions} | {m.status_badge} | {m.verification_gate} | `{ev_display}` |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### 🛡️ Step-Gate Invariant Rules")
        lines.append("1. **Sequential Integrity**: The browser agent is locked from dispatching actions belonging to future steps until the current step attains `✅ PASSED`.")
        lines.append("2. **Human-in-the-Loop Protocol**: Any login barrier halts automation with `🟡 WAITING_USER` until the user supplies credentials in Antigravity.")
        lines.append("3. **Goal-Driven Autonomy**: Testing runs without arbitrary step limits until all milestones are satisfied or explicit user cancellation.")
        lines.append("")
        return "\n".join(lines)

    def persist(self) -> None:
        """Save the rendered tracker to disk."""
        if not self.tracker_path:
            return
        try:
            self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
            self.tracker_path.write_text(self.render_markdown(), encoding="utf-8")
        except Exception:
            pass


__all__ = ["MilestoneStatus", "MilestoneStep", "TaskTracker"]

