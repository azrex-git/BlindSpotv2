"""Markdown report renderer for BlindSpot UX findings and user journeys.

Generates a clean, GitHub-flavored Markdown document summarizing the entire audit,
including executive metrics, persona profiles, step-by-step execution traces, and
prioritized usability/accessibility findings.
"""

from pathlib import Path
from typing import Any, List, Optional

from blindspot.execution.models import ExecutionRunResult
from blindspot.reporting.models import BlindSpotReport, FindingCategory, SeverityLevel, UXFinding


def _severity_icon(severity: SeverityLevel) -> str:
    icons = {
        SeverityLevel.CRITICAL: "🔴 **CRITICAL**",
        SeverityLevel.HIGH: "🟠 **HIGH**",
        SeverityLevel.MEDIUM: "🟡 **MEDIUM**",
        SeverityLevel.LOW: "🔵 **LOW**",
        SeverityLevel.INFORMATIONAL: "⚪ **INFO**",
    }
    return icons.get(severity, str(severity))


def _category_icon(category: FindingCategory) -> str:
    icons = {
        FindingCategory.VERIFIED_ISSUE: "🚨 Objectively Verified Issue",
        FindingCategory.USABILITY_OBSERVATION: "👁️ Usability Observation",
        FindingCategory.POTENTIAL_IMPROVEMENT: "💡 Potential Improvement",
    }
    return icons.get(category, str(category))


def render_markdown_report(
    report: BlindSpotReport,
    execution_result: Optional[ExecutionRunResult] = None,
    output_dir: Optional[Path] = None,
) -> str:
    """Render a comprehensive GitHub-Flavored Markdown audit report."""
    md: List[str] = []

    # Title & Header
    md.append(f"# 🔍 BlindSpot UX & Accessibility Audit Report")
    md.append("")
    md.append(f"> **Report ID:** `{report.report_id}`  ")
    md.append(f"> **Target Website:** [{report.target_url}]({report.target_url})  ")
    md.append(f"> **Generated:** `{report.generated_at}`  ")
    md.append(f"> **Browser Engine:** `{report.browser}` ({'Headless' if report.headless else 'Visible Window'})  ")
    if report.context:
        md.append(f"> **Testing Context:** {report.context}")
    md.append("")
    md.append("---")
    md.append("")

    # 1. Executive Summary & Metrics
    md.append("## 📊 Executive Summary")
    md.append("")
    metrics = report.task_metrics
    md.append("| Metric | Count | Status |")
    md.append("| :--- | :---: | :--- |")
    md.append(f"| **Simulated Personas** | **{metrics.total_personas}** | Configured profiles |")
    md.append(f"| **Total User Tasks** | **{metrics.total_tasks}** | Evaluated browser journeys |")
    md.append(f"| **Passed Tasks** | **{metrics.passed_tasks}** | ✅ Meets observable success criteria |")
    md.append(f"| **Failed Tasks** | **{metrics.failed_tasks}** | ❌ Blocked or hit action limit |")
    md.append(f"| **Inconclusive Tasks** | **{metrics.inconclusive_tasks}** | ⚠️ Partial or unconfirmed completion |")
    md.append("")

    # Findings tally
    verified_cnt = sum(1 for f in report.findings if f.category == FindingCategory.VERIFIED_ISSUE)
    obs_cnt = sum(1 for f in report.findings if f.category == FindingCategory.USABILITY_OBSERVATION)
    imp_cnt = sum(1 for f in report.findings if f.category == FindingCategory.POTENTIAL_IMPROVEMENT)

    md.append("### 🏷️ Identified Usability & Accessibility Findings")
    md.append("")
    md.append(f"- 🚨 **Objectively Verified Issues:** {verified_cnt}")
    md.append(f"- 👁️ **Usability Observations:** {obs_cnt}")
    md.append(f"- 💡 **Potential Improvements:** {imp_cnt}")
    md.append(f"- **Total Identified Findings:** {len(report.findings)}")
    md.append("")
    md.append("---")
    md.append("")

    # 2. Simulated Personas
    if report.personas_summary:
        md.append("## 👥 Simulated User Personas")
        md.append("")
        md.append("| Persona | Experience | Accessibility & Needs | Tasks | Detailed Report |")
        md.append("| :--- | :--- | :--- | :---: | :--- |")
        for p in report.personas_summary:
            p_id = p.get("id", "")
            p_link = "[View in Browser Interaction](browser_interaction.md)" if p_id else "-"
            md.append(f"| **{p.get('name', 'Persona')}** | {p.get('experience', 'Standard')} | {p.get('style_or_needs', 'Standard Desktop')} | {p.get('tasks_count', 0)} | {p_link} |")
        md.append("")
        md.append("---")
        md.append("")

    # 3. User Journey Execution Details
    if execution_result and execution_result.personas:
        md.append("## 🚀 Step-by-Step User Journey Execution")
        md.append("")
        for persona_res in execution_result.personas:
            md.append(f"### Persona: {persona_res.persona_name}")
            md.append("")
            tasks_list = getattr(persona_res, "task_results", None) or getattr(persona_res, "tasks", [])
            for task_res in tasks_list:
                status_badge = "✅ PASSED" if task_res.status.value == "success" else ("❌ FAILED" if task_res.status.value == "failure" else "⚠️ INCONCLUSIVE")
                md.append(f"#### Task: {task_res.task_objective}")
                md.append(f"- **Status:** {status_badge}")
                md.append(f"- **Steps Taken:** {len(task_res.actions_taken)} actions")
                md.append(f"- **Initial URL:** `{task_res.initial_url}`")
                md.append(f"- **Final URL:** `{task_res.final_url}`")
                if task_res.error_message:
                    md.append(f"- **Failure Detail:** {task_res.error_message}")
                if task_res.evidence:
                    md.append(f"- **Observed Evidence:**")
                    for ev in task_res.evidence:
                        md.append(f"  - {ev}")

                # Step details table
                if task_res.actions_taken:
                    md.append("")
                    md.append("| Step | Action | Target / Details | Reasoning | Outcome |")
                    md.append("| :---: | :--- | :--- | :--- | :---: |")
                    for act in task_res.actions_taken:
                        act_type = getattr(act.action, "action", "")
                        if hasattr(act_type, "value"):
                            act_type = act_type.value
                        target = getattr(act.action, "target", "") or ""
                        val = getattr(act.action, "value", "") or getattr(act.action, "text", "") or ""
                        details = f"`{target}` {val}".strip() if target or val else "—"
                        reason = getattr(act.action, "reasoning", "") or ""
                        res_icon = "✓" if act.success else "✖"
                        md.append(f"| {act.step} | **{act_type}** | {details} | {reason} | {res_icon} |")
                md.append("")
        md.append("---")
        md.append("")

    # 4. Prioritized Findings
    md.append("## 🏆 Prioritized UX & Accessibility Findings")
    md.append("")
    if not report.findings:
        md.append("🎉 *No critical UX defects or accessibility violations identified during this session.*")
        md.append("")
    else:
        for idx, finding in enumerate(report.findings, start=1):
            md.append(f"### #{idx}. {finding.title}")
            md.append("")
            md.append(f"- **Severity:** {_severity_icon(finding.severity)}")
            md.append(f"- **Category:** {_category_icon(finding.category)}")
            md.append(f"- **Confidence:** `{int(finding.confidence * 100)}%`")
            if finding.affected_page_url:
                md.append(f"- **Affected URL:** [{finding.affected_page_url}]({finding.affected_page_url})")
            md.append("")
            md.append(f"**Description:**  \n{finding.description}")
            md.append("")

            if finding.supporting_evidence:
                md.append("**Supporting Evidence:**")
                for ev in finding.supporting_evidence:
                    md.append(f"- {ev}")
                md.append("")

            if finding.reproduction_steps:
                md.append("**Reproduction Steps:**")
                for step_idx, step_desc in enumerate(finding.reproduction_steps, start=1):
                    md.append(f"{step_idx}. {step_desc}")
                md.append("")

            if finding.suggested_improvement:
                md.append(f"> 💡 **Suggested Remediation:**  \n> {finding.suggested_improvement}")
                if finding.expected_benefit:
                    md.append(f"> \n> **Expected User Benefit:** {finding.expected_benefit}")
                md.append("")

            md.append("---")
            md.append("")

    # 5. Technical Inspection Summary
    insp = report.inspection_summary
    if insp:
        md.append("## 🛠️ Technical & DOM Inspection Summary")
        md.append("")
        md.append(f"- **Page Title:** `{insp.get('title', 'Unknown')}`")
        md.append(f"- **Final URL:** [{insp.get('final_url', report.target_url)}]({insp.get('final_url', report.target_url)})")
        md.append(f"- **Total Interactive Elements:** `{insp.get('total_interactive_elements', 0)}`")
        md.append(f"  - Links: `{insp.get('links_count', 0)}`")
        md.append(f"  - Buttons: `{insp.get('buttons_count', 0)}`")
        md.append(f"  - Form Inputs / Fields: `{insp.get('form_fields_count', 0)}`")
        vp = insp.get("viewport", {})
        if vp:
            md.append(f"- **Tested Viewport:** `{vp.get('width', 1280)}x{vp.get('height', 800)}`")
        md.append("")

    # Footer
    md.append("---")
    md.append("*Generated automatically by BlindSpot Autonomous UX & Accessibility Audit Agent.*")
    md.append("")

    return "\n".join(md)


def render_persona_markdown_report(
    persona: Any,
    task_results: List[Any],
    target_url: str,
    context: Optional[str] = None,
    findings: Optional[List[UXFinding]] = None,
) -> str:
    """Render a dedicated, detailed Markdown report for an individual persona journey."""
    md: List[str] = []

    passed_count = sum(1 for t in task_results if getattr(t, "status", None) and getattr(t.status, "value", str(t.status)).lower() == "success")
    failed_count = sum(1 for t in task_results if getattr(t, "status", None) and getattr(t.status, "value", str(t.status)).lower() == "failure")
    inconclusive_count = sum(1 for t in task_results if getattr(t, "status", None) and getattr(t.status, "value", str(t.status)).lower() == "inconclusive")

    md.append(f"# 👤 Persona UX Journey Report: {persona.name}")
    md.append("")
    md.append(f"> **Target Website:** [{target_url}]({target_url})  ")
    md.append(f"> **Experience Level:** `{persona.experience_level}`  ")
    md.append(f"> **Accessibility & Device:** `{getattr(persona, 'accessibility_needs', None) or 'Standard'}`  ")
    if context:
        md.append(f"> **Audit Context:** {context}  ")
    md.append(f"> **Overall Outcome:** **{passed_count} Passed**, **{failed_count} Failed**, **{inconclusive_count} Inconclusive**")
    md.append("")
    md.append("---")
    md.append("")

    # 1. Persona Profile & Background
    md.append("## 🎯 Persona Profile & Intent")
    md.append("")
    md.append(f"**Background:**  \n{persona.description}")
    md.append("")
    if persona.goals:
        md.append("**Primary User Goals:**")
        for g in persona.goals:
            md.append(f"- {g}")
        md.append("")
    if getattr(persona, "likely_difficulties", None):
        md.append("**Anticipated Usability Friction:**")
        for d in persona.likely_difficulties:
            md.append(f"- {d}")
        md.append("")

    md.append("---")
    md.append("")

    # 2. Task Journeys
    md.append("## 🚀 Task Execution Journeys")
    md.append("")
    if not task_results:
        md.append("*(No browser tasks executed for this persona)*")
        md.append("")
    else:
        for idx, task in enumerate(task_results, start=1):
            status_val = getattr(task.status, "value", str(task.status)).lower()
            status_badge = "✅ **PASSED**" if status_val == "success" else ("❌ **FAILED**" if status_val == "failure" else "⚠️ **INCONCLUSIVE**")

            obj = getattr(task, "task_objective", getattr(task, "objective", "User task"))
            md.append(f"### Task {idx}: {obj}")
            md.append("")
            md.append(f"- **Status:** {status_badge}")
            history = getattr(task, "history", [])
            md.append(f"- **Steps Taken:** {len(history)} browser actions")
            md.append(f"- **Initial URL:** `{getattr(task, 'initial_url', target_url)}`")
            md.append(f"- **Final URL:** `{getattr(task, 'final_url', target_url)}`")
            if getattr(task, "error_message", None):
                md.append(f"- **Error Encountered:** `{task.error_message}`")
            md.append("")

            # Action trail
            if history:
                md.append("#### 🎬 Step-by-Step Action Trail:")
                for h in history:
                    act_obj = getattr(h, "action", None)
                    act_type = getattr(getattr(act_obj, "action", None), "value", str(getattr(act_obj, "action", "action"))).upper() if act_obj else "ACTION"
                    target_info = f" on `{act_obj.target}`" if act_obj and getattr(act_obj, "target", None) else ""
                    val_info = f" with value `\"{act_obj.value}\"`" if act_obj and getattr(act_obj, "value", None) else ""
                    step_status = "✓" if getattr(h, "success", True) else "✖"
                    step_num = getattr(h, "step", "?")
                    md.append(f"{step_num}. **[{step_status}] {act_type}**{target_info}{val_info}")
                    if act_obj and getattr(act_obj, "reasoning", None):
                        md.append(f"   - *Thought:* {act_obj.reasoning}")
                    if getattr(h, "error_message", None):
                        md.append(f"   - *Failure:* `{h.error_message}`")
                md.append("")

            # Evidence
            ev_list = getattr(task, "collected_evidence", getattr(task, "evidence", []))
            if ev_list:
                md.append("#### 📸 Observed Page Evidence:")
                for ev in ev_list:
                    md.append(f"- {ev}")
                md.append("")

            screenshots = getattr(task, "evidence_screenshots", [])
            if screenshots:
                md.append("#### 🖼️ Captured Screenshots:")
                task_id = getattr(task, "task_id", getattr(task, "id", f"task_{idx}"))
                for sc in screenshots:
                    sc_name = Path(sc).name
                    md.append(f"- [{sc_name}](evidence/{task_id}/{sc_name})")
                md.append("")

            md.append("---")
            md.append("")

    # Relevant findings
    if findings:
        p_name_lower = persona.name.lower()
        p_id_lower = persona.id.lower()
        persona_findings = [
            f for f in findings
            if p_id_lower in f.title.lower() or p_id_lower in f.description.lower() or p_name_lower in f.description.lower()
        ]
        if persona_findings:
            md.append("## ⚠️ Usability Issues Affecting This Persona")
            md.append("")
            for f in persona_findings:
                md.append(f"### {_severity_icon(f.severity)} {f.title}")
                md.append(f"- **Category:** {_category_icon(f.category)}")
                md.append(f"- **Description:** {f.description}")
                if f.suggested_improvement:
                    md.append(f"- **Remediation:** {f.suggested_improvement}")
                md.append("")
            md.append("---")
            md.append("")

    # Footer
    md.append("[← Back to Main Executive Summary Report](../../report.md)  ")
    md.append("*Generated automatically by BlindSpot Autonomous UX & Accessibility Audit Agent.*")
    md.append("")

    return "\n".join(md)


def render_persona_profile_markdown(persona) -> str:
    """Render a standalone Markdown persona specification card."""
    md: List[str] = [
        f"# 👤 Persona Profile: {persona.name}",
        "",
        f"> **Identifier:** `{persona.id}`  ",
        f"> **Experience Level:** `{persona.experience_level}`  ",
        f"> **Accessibility & Needs:** `{getattr(persona, 'accessibility_needs', None) or 'Standard Desktop'}`  ",
        "",
        "## 📝 Overview & Background",
        "",
        f"{persona.description}",
        "",
    ]
    if getattr(persona, "goals", None):
        md.append("## 🎯 Goals")
        for g in persona.goals:
            md.append(f"- {g}")
        md.append("")

    if getattr(persona, "likely_difficulties", None):
        md.append("## ⚠️ Anticipated Usability & Friction Points")
        for d in persona.likely_difficulties:
            md.append(f"- {d}")
        md.append("")

    if getattr(persona, "tasks", None):
        md.append("## 📋 Assigned Tasks")
        for idx, t in enumerate(persona.tasks, start=1):
            md.append(f"### {idx}. {t.objective}")
            md.append(f"- **Starting Conditions:** {t.starting_conditions}")
            if t.success_criteria:
                md.append(f"- **Observable Success Criteria:** {', '.join(t.success_criteria)}")
            if t.evidence_to_collect:
                md.append(f"- **Evidence to Collect:** {', '.join(t.evidence_to_collect)}")
            md.append("")

    return "\n".join(md)


def render_persona_journey_log_markdown(persona, task_results: list, target_url: str = "") -> str:
    """Render a chronological action log and thought trace for this persona's browsing session."""
    md: List[str] = [
        f"# 🎬 Persona Journey Log: {persona.name}",
        "",
        f"> **Target URL:** {target_url}  ",
        f"> **Persona ID:** `{persona.id}`  ",
        "",
        "---",
        "",
    ]
    if not task_results:
        md.append("*(No actions recorded)*\n")
        return "\n".join(md)

    for idx, task in enumerate(task_results, start=1):
        obj = getattr(task, "task_objective", getattr(task, "objective", f"Task {idx}"))
        status_val = getattr(task.status, "value", str(task.status)).lower()
        status_badge = "✅ PASSED" if status_val == "success" else ("❌ FAILED" if status_val == "failure" else "⚠️ INCONCLUSIVE")
        md.append(f"## Task {idx}: {obj}")
        md.append(f"**Outcome:** `{status_badge}`  ")
        md.append(f"**Initial URL:** `{getattr(task, 'initial_url', target_url)}`  ")
        md.append(f"**Final URL:** `{getattr(task, 'final_url', target_url)}`  ")
        if getattr(task, "error_message", None):
            md.append(f"**Error:** `{task.error_message}`  ")
        md.append("")

        history = getattr(task, "history", [])
        if history:
            md.append("### Chronological Action Trail")
            md.append("")
            md.append("| Step | Status | Action | Target / Selector | Value | Persona Thought / Observation |")
            md.append("| :---: | :---: | :--- | :--- | :--- | :--- |")
            for h in history:
                step_num = getattr(h, "step", "?")
                st = "✅" if getattr(h, "success", True) else "❌"
                act_obj = getattr(h, "action", None)
                act_name = getattr(getattr(act_obj, "action", None), "value", str(getattr(act_obj, "action", "action"))).upper() if act_obj else "ACTION"
                target_str = f"`{act_obj.target}`" if act_obj and getattr(act_obj, "target", None) else "-"
                val_str = f"`{act_obj.value}`" if act_obj and getattr(act_obj, "value", None) else "-"
                thought_str = getattr(act_obj, "reasoning", "") or "-"
                md.append(f"| {step_num} | {st} | **{act_name}** | {target_str} | {val_str} | {thought_str} |")
            md.append("")

        ev_list = getattr(task, "collected_evidence", getattr(task, "evidence", []))
        if ev_list:
            md.append("### Observed Page Evidence")
            for ev in ev_list:
                md.append(f"- {ev}")
            md.append("")

        md.append("---")
        md.append("")

    return "\n".join(md)


def render_persona_findings_markdown(persona, findings: list) -> str:
    """Render findings, visual bugs, and UX issues that specifically impacted this persona."""
    md: List[str] = [
        f"# ⚠️ Usability & Visual Findings: {persona.name}",
        "",
        f"> **Persona ID:** `{persona.id}`  ",
        f"> **Persona Type:** `{persona.experience_level}`  ",
        "",
        "---",
        "",
    ]
    p_name_lower = persona.name.lower()
    p_id_lower = persona.id.lower()
    persona_findings = [
        f for f in findings
        if p_id_lower in f.title.lower() or p_id_lower in f.description.lower() or p_name_lower in f.description.lower()
    ]

    if not persona_findings:
        md.append("✅ **No severe usability barriers or critical visual defects blocked this persona's primary tasks.**")
        md.append("")
        return "\n".join(md)

    for idx, f in enumerate(persona_findings, start=1):
        md.append(f"## {idx}. {_severity_icon(f.severity)} {f.title}")
        md.append("")
        md.append(f"- **Category:** {_category_icon(f.category)}")
        md.append(f"- **Description:** {f.description}")
        if getattr(f, "wcag_criterion", None):
            md.append(f"- **WCAG Standard:** `{f.wcag_criterion}`")
        if getattr(f, "suggested_improvement", None):
            md.append(f"- **Recommended Fix:** {f.suggested_improvement}")
        if getattr(f, "code_recommendation", None):
            md.append("")
            md.append("```css")
            md.append(f.code_recommendation.strip())
            md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    return "\n".join(md)

