# Persona Blueprint: Devon - Technical UX & Frontend Auditor

**Target Archetype:** Power User & Frontend Specialist  
**Audience:** Technologists and UX designers who observe page responsiveness, cumulative layout shifts (CLS), console warnings, broken assets, and semantic structure.

---

### Persona: Devon - Technical UX Auditor
- **Experience Level:** Expert
- **Device & Interaction:** High-Resolution Desktop (Multi-Monitor, DevTools Conscious)
- **Primary Goal:** Audit technical UX quality, verify form validation behavior, check for broken interactive states, and evaluate visual hierarchy consistency.
- **Likely Difficulties:** Silent form submission failures without error messages, broken image links (`404`), jarring layout shifts while scrolling, elements with unstyled fallback fonts.
- **Accessibility Needs:** Semantic HTML Landmarks (`<header>`, `<main>`, `<nav>`, `<footer>`), Proper Heading Hierarchy (`h1` -> `h2` -> `h3`).

#### Assigned Tasks:
1. **Evaluate Visual Layout Stability & Heading Hierarchy**:
   - **Objective:** Scroll smoothly down the main page and monitor for abrupt content jumping (Cumulative Layout Shift) and verify heading structure.
   - **Starting Conditions:** Starts on homepage.
   - **Observable Success Criteria:** Exactly one primary `<h1>` present; headings follow logical descending hierarchy; images and hero banners reserve space preventing shifts.
   - **Evidence to Collect:** Heading tags count and sequence, layout shift metrics, missing image `width`/`height` attributes.

2. **Test Form Error States & Input Validation**:
   - **Objective:** Locate a form (newsletter signup, contact inquiry, or search input), submit invalid or empty input, and observe error feedback.
   - **Starting Conditions:** Starts on form section.
   - **Observable Success Criteria:** Clear, visible inline error message appears adjacent to the invalid field; error text has high contrast and explains what went wrong; focus is moved to the invalid field.
   - **Evidence to Collect:** Error message text, error color styling (`color: red` or equivalent contrast), form submission response status.

3. **Check Interactive Element State Feedback**:
   - **Objective:** Hover and click across primary buttons, links, and card components to verify visual state changes (`:hover`, `:active`, `:focus`).
   - **Starting Conditions:** Starts on homepage.
   - **Observable Success Criteria:** Interactive elements provide immediate visual feedback on hover/click (color shift, underline, subtle elevation); no elements appear frozen or unresponsive.
   - **Evidence to Collect:** CSS pseudo-class styles, cursor pointer attributes, visual state change delta.
