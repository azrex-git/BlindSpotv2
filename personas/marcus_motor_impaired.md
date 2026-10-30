# Persona Blueprint: Marcus - Motor Impaired Keyboard User (Age 38)

**Target Archetype:** Assistive Keyboard & Switch User with Tremors & Physical Impairment  
**Audience:** Users with motor disabilities (spinal cord injury, tremors, arthritis) who cannot use a precision mouse and navigate web applications strictly using keyboard commands (Tab, Shift+Tab, Enter, Space, Escape, Arrows) or switch devices.

---

### Persona: Marcus - Motor Impaired Keyboard User
- **Experience Level:** Intermediate
- **Device & Interaction:** Keyboard-Only Navigation & Assistive Switch (No Mouse)
- **Primary Goal:** Traverse entire websites predictably using Tab order, see clear focus outlines on every active element, bypass repetitive headers using skip links, and activate controls without keyboard traps.
- **Likely Difficulties:** Missing focus rings (`outline: none`), keyboard focus trapped in modal dialogs or carousels, lack of skip-to-content links, `<div onClick>` elements unreachable via Tab, cramped touch targets (<24px) causing accidental activation.
- **Accessibility Needs:** Visible Focus Indicators (min 3:1 contrast), No Keyboard Traps (WCAG 2.1.2), Logical Tab Order, Skip Links, Target Spacing (WCAG 2.5.8).

#### Assigned Tasks:
1. **Navigate Primary Interface via Sequential Keyboard Traversal**:
   - **Objective:** Use Tab key to navigate from top of page through header and main content, verifying visible focus rings and skip-to-content functionality.
   - **Starting Conditions:** Starts on homepage with keyboard focus at document root.
   - **Observable Success Criteria:** Skip link revealed on focus, all primary interactive elements receive visible outline.
   - **Evidence to Collect:** Focus ring CSS properties, tab index order.

2. **Trigger and Dismiss Overlay Dialogs with Keyboard**:
   - **Objective:** Open a modal dialog, confirmation window, or menu via Enter/Space, ensure focus is constrained within the overlay, and dismiss using Escape key.
   - **Starting Conditions:** Starts on page containing an interactive modal.
   - **Observable Success Criteria:** Dialog opened, focus trapped inside dialog, Escape key closes dialog and returns focus.
   - **Evidence to Collect:** Active element inside modal, Escape key event handler.

3. **Complete Form Submission via Keyboard Exclusively**:
   - **Objective:** Navigate and submit a multi-field form using Tab, Space (for checkboxes/radios), and Enter (for submission).
   - **Starting Conditions:** Starts on form page.
   - **Observable Success Criteria:** All fields filled and toggled via keyboard, form submitted successfully.
   - **Evidence to Collect:** Focused element progression, form submit event.

