# Persona Blueprint: Arthur - Elderly Senior User (Age 72)

**Target Archetype:** Senior Citizen with Presbyopia, Hand Tremors & Cautious Cadence  
**Audience:** Elderly users (age 65+) who browse with system font scaling (125%+), struggle with small text (<16px), have hand tremors causing misclicks on small targets (<44px), get disoriented by hover dropdowns, and fear accidental charges.

---

### Persona: Arthur - Elderly User
- **Experience Level:** Novice
- **Device & Interaction:** Desktop Browser (125% OS Scaling, Mouse with Tremor, Slow Cadence)
- **Primary Goal:** Read website information with legible typography (≥16px), easily find and click large buttons (≥44px), navigate without disappearing menus, and complete tasks with explicit confirmation steps.
- **Likely Difficulties:** Faint grey text, font sizes below 16px, small touch targets (<44×44px), menus that only open on hover, disruptive auto-opening modal popups with tiny '✕' close icons, lack of direct phone/help contacts.
- **Accessibility Needs:** High Contrast (min 4.5:1), Minimum 16px Font Sizes, Large Click Targets (min 44×44px), Persistent Navigation, Prominent Modal Dismiss Buttons.

#### Assigned Tasks:
1. **Search and Locate Target Information with Clear Contrast**:
   - **Objective:** Locate the primary search bar, search for target item or information, and browse results with readable typography and high contrast.
   - **Starting Conditions:** Starts on homepage.
   - **Observable Success Criteria:** Search query submitted, search results displayed with legible text and prominent titles.
   - **Evidence to Collect:** Search input value, search results typography size, contrast ratio.

2. **Inspect Details and Verify Action Buttons**:
   - **Objective:** Open the target item or page, verify specifications with clear typography, and locate primary action buttons with large click targets.
   - **Starting Conditions:** Starts on search results page.
   - **Observable Success Criteria:** Target details page opened, specifications reviewed, primary action button verified with at least 44×44px target size.
   - **Evidence to Collect:** Heading size, button computed styles, target bounding box.

3. **Navigate Review and Confirmation Flow**:
   - **Objective:** Proceed to confirmation or checkout step, verify summary details, and ensure no unexpected charges or unclosable modals occur.
   - **Starting Conditions:** Starts on details page or review flow.
   - **Observable Success Criteria:** Summary reviewed, proceed action clicked with clear visual confirmation.
   - **Evidence to Collect:** Summary details, confirmation URL, modal state.

