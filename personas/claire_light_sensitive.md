# Persona Blueprint: Claire - Light Sensitive & Photophobic User (Age 42)

**Target Archetype:** Photophobic & Sensory Sensitive User with Vestibular Migraines  
**Audience:** Users with photophobia, ocular migraines, dry eye disease, or vestibular sensitivity who suffer eye pain, nausea, and disorientation from glaring white backgrounds, auto-playing video/canvas animations, and strobing carousels.

---

### Persona: Claire - Light Sensitive User
- **Experience Level:** Intermediate
- **Device & Interaction:** Desktop Browser with OS Dark Mode & Prefers-Reduced-Motion Enabled
- **Primary Goal:** Browse comfortably without blinding glare, switch to dark mode, easily pause auto-playing media, and experience static or gentle transitions.
- **Likely Difficulties:** Stark `#FFFFFF` monolithic white surfaces with no dark theme toggle, ambient background video looping without a pause button, parallax scrolling triggering vertigo, carousels auto-advancing every few seconds, strobing/flashing elements.
- **Accessibility Needs:** Dark Mode / Theme Options, WCAG 2.2.2 (Pause, Stop, Hide Controls for Moving Content), WCAG 2.3.3 (Respect Prefers-Reduced-Motion), WCAG 2.3.1 (No Flashing >3/sec).

#### Assigned Tasks:
1. **Locate and Activate Dark Mode / Theme Option**:
   - **Objective:** Locate a dark mode or theme switcher upon landing on a bright white website to reduce visual glare and fatigue.
   - **Starting Conditions:** Starts on homepage with `prefers-color-scheme: dark` set at OS level.
   - **Observable Success Criteria:** Dark theme automatically honored or theme toggle easily accessible in header/footer.
   - **Evidence to Collect:** Background color hex, theme toggle element presence.

2. **Verify Media Controls on Auto-Playing Videos and Carousels**:
   - **Objective:** Check that any auto-playing hero video, animated banner, or carousel provides a visible, accessible Pause or Stop button.
   - **Starting Conditions:** Starts on media-rich page or hero section.
   - **Observable Success Criteria:** Video or animation has accessible pause control, or does not auto-play.
   - **Evidence to Collect:** Video element attributes, pause button selector.

3. **Verify Motion Reduction Compliance**:
   - **Objective:** Scroll through page sections to ensure animations, parallax scrolling, and layout transitions are suppressed when reduced-motion is requested.
   - **Starting Conditions:** Starts on interactive page with animations.
   - **Observable Success Criteria:** Parallax and floating animations disabled or simplified per `@media (prefers-reduced-motion)`.
   - **Evidence to Collect:** CSS animation rules, scroll behavior.

