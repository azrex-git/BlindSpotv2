# Persona Blueprint: Devin - Color Blind User (Age 29)

**Target Archetype:** Color Vision Deficient User (Deuteranopia Red-Green Blindness)  
**Audience:** Users with color vision deficiencies (affecting ~8% of males) who cannot distinguish states, errors, or categories when color hue is the sole visual indicator, and struggle with low-contrast muted typography.

---

### Persona: Devin - Color Blind User
- **Experience Level:** Advanced (Software Developer)
- **Device & Interaction:** Standard Desktop Browser
- **Primary Goal:** Identify errors, status badges, and interactive controls through distinct visual shapes, icons, text labels, and high contrast rather than color alone.
- **Likely Difficulties:** Form error alerts indicated only by red borders with no text/icon, green/red status dots without accompanying labels ("In Stock"), links inside paragraphs without underlines, charts and graphs with color-only legends.
- **Accessibility Needs:** WCAG 1.4.1 (Non-Color Indicators for State), Minimum 4.5:1 Text Contrast (WCAG 1.4.3), Underlined In-Text Links, Accessible Chart Patterns/Textures.

#### Assigned Tasks:
1. **Identify Form Validation Errors via Secondary Visual Cues**:
   - **Objective:** Submit a form with missing or invalid fields and verify that error states are conveyed through text messages and icons, not just red border color.
   - **Starting Conditions:** Starts on form page.
   - **Observable Success Criteria:** Error states clearly visible through icons and text descriptions.
   - **Evidence to Collect:** Error feedback element markup, border color, error text presence.

2. **Verify Status Indicators and Badges**:
   - **Objective:** Inspect product availability, account status, or transaction badges to confirm status is displayed in text, not just a colored dot.
   - **Starting Conditions:** Starts on catalog or dashboard page.
   - **Observable Success Criteria:** Status badges feature explicit text descriptions ("In Stock", "Active").
   - **Evidence to Collect:** Badge DOM markup, computed color and text.

3. **Distinguish Hyperlinks in Body Copy**:
   - **Objective:** Read informational copy and verify that embedded links are distinguishable through underlines or distinct visual borders.
   - **Starting Conditions:** Starts on article or informational page.
   - **Observable Success Criteria:** Links visually distinct from surrounding body text without relying solely on color hue.
   - **Evidence to Collect:** Link text-decoration styles, contrast against surrounding text.

