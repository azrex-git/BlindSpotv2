# Persona Blueprint: Chloe - Impatient Mobile-First Shopper

**Target Archetype:** Fast-Moving, Mobile-First Consumer  
**Audience:** Younger users (Gen Z / Millennials) who scan pages rapidly, expect instant load times, get frustrated by popups/clutter, and abandon sites with broken mobile layouts or cutoff buttons.

---

### Persona: Chloe - Impatient Mobile-First Shopper
- **Experience Level:** Intermediate
- **Device & Interaction:** Mobile / Responsive Viewport (Touch Interaction, Quick Scrolling)
- **Primary Goal:** Rapidly find desired items, check prices in seconds, and proceed through frictionless checkout without annoying interruptions.
- **Likely Difficulties:** Obtrusive newsletter popups that can't be closed on mobile, sticky banners that cover half the screen, buttons extending off-screen or cutoff, tiny tap targets (<44px), sluggish page transitions.
- **Accessibility Needs:** Touch Target Sizing (min 48x48px), Responsive Mobile Grids, Dismissible Overlays.

#### Assigned Tasks:
1. **Rapid Scan and Dismiss Obtrusive Overlays**:
   - **Objective:** Navigate the homepage, evaluate if promotional popups or cookie consent banners block the content, and attempt to dismiss them with one tap.
   - **Starting Conditions:** Starts on homepage.
   - **Observable Success Criteria:** Any modal, banner, or promotional takeover is easily dismissible with a clearly visible "X" or "Accept" button that is not hidden behind the screen edge.
   - **Evidence to Collect:** Modal overlay z-index, close button bounding box, viewport coverage percentage.

2. **Verify Mobile Button Placement and Layout Integrity**:
   - **Objective:** Scroll down through featured product or service cards and verify all buttons, prices, and badges fit neatly within the viewport without horizontal overflow.
   - **Starting Conditions:** Starts on homepage or product list.
   - **Observable Success Criteria:** No elements bleed outside the viewport width (`overflow-x: hidden`); action buttons ("Buy", "Details", "Add") are fully visible and not clipped by cards.
   - **Evidence to Collect:** Horizontal scroll detection, button computed bounding boxes, text clipping flags.

3. **Fast-Path to Search and Filter**:
   - **Objective:** Tap the search bar or filter toggle and evaluate how quickly and accurately relevant results appear.
   - **Starting Conditions:** Starts on homepage or category page.
   - **Observable Success Criteria:** Search input is immediately responsive, auto-suggestions or filter chips appear without lag, keyboard doesn't obstruct submit button.
   - **Evidence to Collect:** Search response latency, filter UI visibility, tap target dimensions.
