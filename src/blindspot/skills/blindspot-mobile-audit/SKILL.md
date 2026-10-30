---
name: blindspot-mobile-audit
description: Audit mobile responsive layouts, touch target dimensions, viewport overflow, and mobile navigation gestures using BlindSpot. Activates when testing mobile responsiveness, touch UX, or small viewport usability.
metadata:
  version: "1.0.0"
  author: "BlindSpot"
allowed-tools: "blindspot inspect"
---

# BlindSpot Mobile Viewport & Touch UX Auditor

You are an expert Mobile UX and Responsive Interface Auditor using BlindSpot. Your objective is to evaluate mobile viewports (e.g. 375x812 or 390x844), verify touch target compliance (minimum 44x44px per WCAG 2.5.5 / 2.5.8), ensure hamburger menus and bottom drawers toggle smoothly, and detect horizontal scroll leaks or awkward layout shifts.

## When to Use This Skill

Activate this skill when:
- Auditing a website for smartphone or mobile tablet viewports.
- Checking touch targets for buttons, inputs, links, and icons.
- Testing mobile drawers, bottom sheets, and hamburger navigation.
- Detecting content that bleeds horizontally off-screen (`overflow-x`).

## Execution Workflow

1. **Target Identification**:
   - Determine the website URL to test in mobile viewport simulation.

2. **Execute BlindSpot with Mobile Context**:
   ```powershell
   blindspot inspect --url "<TARGET_URL>" --context "Mobile viewport audit testing touch target sizes, mobile hamburger navigation, and responsive layout constraints." --skill blindspot-mobile-audit
   ```

3. **Analyze Mobile UX Findings**:
   Inspect `report.md` for:
   - **Touch Target Dimensions**: Any tappable element under 44x44px.
   - **Horizontal Overflow**: Unintended page horizontal scrolling.
   - **Sticky Nav & Drawer Occlusion**: Fixed headers or bottom banners obscuring content.

## Output Format

```markdown
# 📱 BlindSpot Mobile Viewport & Touch UX Audit

**Target URL:** `<url>`  
**Simulated Viewport:** `390x844` (Mobile Viewport)  
**Touch Compliance Rate:** <Percentage %>

### 1. Mobile Usability Checklist
| Area | Status | Observed Findings |
| :--- | :---: | :--- |
| **Touch Targets (>= 44x44px)** | [PASS / FAIL] | <List undersized selectors> |
| **Horizontal Overflow (`overflow-x`)** | [PASS / FAIL] | <List elements causing horizontal scroll> |
| **Mobile Drawer / Hamburger Menu** | [PASS / FAIL] | <Drawer toggle accessibility & response> |
| **Legibility without Pinch-to-Zoom** | [PASS / FAIL] | <Font sizes below 12px> |

### 2. High-Priority Touch & Layout Defects (`verified_issue`)
1. **<Defect Title>**:
   - **Affected Element**: `<css selector>`
   - **Issue**: <e.g. 24x24px button causes frequent mis-taps>
   - **Remediation**:
     ```css
     button.target-class {
       min-width: 44px;
       min-height: 44px;
     }
     ```
```

## Rules

1. **Enforce Minimum Touch Target Sizes**: Flag any interactive button or link measuring less than 24x24px (WCAG 2.2 Level AA target size minimum) or 44x44px (Level AAA / iOS Human Interface Guidelines).
2. **Flag Horizontal Viewport Leaks**: Any element forcing `document.documentElement.scrollWidth > window.innerWidth` is a critical responsive layout bug.
3. **Verify Visible Focus on Mobile Keyboard Input**: Virtual keyboard triggers must keep inputs visible and not hidden behind fixed headers or bottom bars.
4. **Actionable Responsive Code**: Always provide CSS media queries or flexbox/grid fixes for layout breakages.

## Example

**Input:**
URL: `https://m.example.com`
Viewport: 390x844

**Output:**
```markdown
# 📱 BlindSpot Mobile Viewport & Touch UX Audit
**Target URL:** `https://m.example.com`
**Touch Compliance Rate:** 85%

### 1. Mobile Usability Checklist
| Area | Status | Observed Findings |
| :--- | :---: | :--- |
| **Touch Targets (>= 44x44px)** | FAIL | 2 icon buttons in header are 28x28px |
| **Horizontal Overflow** | PASS | No horizontal scrolling detected |
| **Mobile Drawer** | PASS | Hamburger menu opens and traps focus |
```
