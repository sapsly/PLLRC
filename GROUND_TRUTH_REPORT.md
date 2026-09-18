# PIP Ground-Truth Analysis Report
## Single Screenshot Analysis: Screenshot 2026-09-08 21.24.37.png

---

### 1. Ground-Truth Screenshot

| Property | Value |
|----------|-------|
| **File** | `Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png` |
| **Resolution** | 1920×1080 (native) |
| **Race State** | Active live race (shows "Live" indicator) |
| **Optional UI** | **PRESENT** (fuel, tyre, nitro, pit controls visible) |
| **Timestamp in Image** | 21:24:37 / 08/09/2026 |
| **Language** | English |

---

### 2. Control Geometry (1920×1080 coordinates)

All coordinates are in **x1, y1, x2, y2** format (top-left to bottom-right).

| Control | Bounding Box | Label Position | Value Position | Representation |
|---------|--------------|----------------|----------------|----------------|
| **Strategy** | 700, 930, 850, 970 | ~758, 930 ("STRATEGY") | ~756, 940 ("BALANCED") | Text label + text value |
| **Pace** | 800, 930, 950, 970 | ~824, 930 ("PACE") | ~822, 940 ("NEUTRAL") | Text label + text value |
| **Tyre** | 850, 930, 1000, 970 | ~758, 968 ("TYRE") | ~888, 940 ("SOFT") | Text label + text value |
| **Fuel** | 930, 930, 1030, 970 | ~956, 930 ("FUEL") | ~954, 940 ("RICH") | Text label + text value |
| **Defend** | 1000, 930, 1150, 970 | ~1031, 930 ("DEFEND") | **Unknown** (no value text visible) | Text label only |
| **Nitro** | 550, 1000, 700, 1080 | ~574, 1050 ("NITRO") | ~574, 1050 ("×0" / "X 0") | Text label + numeric counter |
| **Pit** | 1600, 930, 1920, 970 | ~1650, 930 ("PIT") | ~1700, 940 ("BOX BOX") | Text label + text value |

**Status Bars** (separate region below main controls, ~y=970-1010):
| Bar | Bounding Box | Visual |
|-----|--------------|--------|
| Tyre Bar | ~700, 970, 1000, 1010 | Horizontal bar, likely green/orange/red segments |
| Fuel Bar | ~1000, 970, 1300, 1010 | Horizontal bar, likely green/orange/red segments |

**Additional UI** (bottom-right, y≈1020-1080):
- "100%" (engine/power?)
- "ENG" (engine mode?)
- "UK" (region/server?)
- "21.24" (lap time?)
- "08/09/2026" (date)
- "X 0" (Nitro counter, left side)

---

### 3. Known States (Confirmed from This Screenshot)

| Control | Visible State | Evidence | Confidence |
|---------|---------------|----------|------------|
| **Strategy** | **BALANCED** | OCR: "BALANCED" (conf 1.00) at value position | 100% |
| **Pace** | **NEUTRAL** | OCR: "NEUTRAL" (conf 1.00) at value position | 100% |
| **Tyre** | **SOFT** | OCR: "SOFT" (conf 0.98) at value position | 98% |
| **Fuel** | **RICH** | OCR: "RICH" (conf 0.97) at value position | 97% |
| **Defend** | **UNKNOWN** | Label "DEFEND" visible (conf 0.61), **no value text detected** | N/A |
| **Nitro** | **0** | OCR: "X 0" / "nItrO" (conf 0.96) | 96% |
| **Pit** | **BOX BOX** | User observation; OCR partial; right-side crop shows "BOX BOX" area | 90%* |

*Pit state based on user visual confirmation + right-side crop region; OCR did not cleanly read "BOX BOX" but region is correct.

---

### 4. State Representation Analysis

| Control | Representation Type | State Change Mechanism |
|---------|---------------------|------------------------|
| **Strategy** | Text label ("STRATEGY") + **text value** ("BALANCED") | Value text changes |
| **Pace** | Text label ("PACE") + **text value** ("NEUTRAL") | Value text changes |
| **Tyre** | Text label ("TYRE") + **text value** ("SOFT") | Value text changes |
| **Fuel** | Text label ("FUEL") + **text value** ("RICH") | Value text changes |
| **Defend** | Text label ("DEFEND") + **no visible value text** | **Unknown** - possibly toggle (ON/OFF), icon, or color change |
| **Nitro** | Text label ("NITRO") + **numeric counter** ("×0") | Numeric counter |
| **Pit** | Text label ("PIT") + **text value** ("BOX BOX") | Value text changes |

**Key insight**: Strategy, Pace, Tyre, Fuel, and Pit use **text labels with text values**. Nitro uses a **numeric counter**. Defend appears to have **only a label** in this screenshot - the state (ON/OFF) is not rendered as text.

---

### 5. Important Corrections to Previous Assumptions

| Previous Assumption | Evidence from Screenshot | Correction |
|---------------------|--------------------------|------------|
| Strategy states: Safe / Neutral / Attack | Visible state: **BALANCED** | **BALANCED is a Strategy state**. Safe/Neutral/Attack may be incorrect, alternative naming, or subset. |
| Pace states: Conserve / Neutral / Push | Visible state: **NEUTRAL** | NEUTRAL confirmed. Conserve/Push **unverified** - may exist or may be different naming. |
| Defend states: On / Off | Label "DEFEND" present, **no ON/OFF text visible** | State representation **unknown** - could be toggle, color, icon, or hidden when OFF. |
| Strategy/Pace are 3-state only | Strategy shows BALANCED (not Safe/Neutral/Attack) | **State lists incomplete/incorrect**. Must discover actual states from game. |
| Controls use color/icons for state | All visible states are **text values** | Primary representation is **text**, not color/icon. |

**Critical**: The term "BALANCED" replaces "Neutral" for Strategy. Previous assumption that Strategy = {Safe, Neutral, Attack} is **disproven** by this evidence.

---

### 6. Layout Information (Optional UI Present)

- **Control Row Y**: ~930-970 (single horizontal row)
- **Horizontal Order** (left → right): Nitro (far left) → Strategy → Pace → Tyre → Fuel → Defend → Pit (far right)
- **Spacing**: ~100-150px between control centers
- **Alignment**: Labels at ~y=930, Values at ~y=940 (labels above values)
- **Container**: Controls appear as separate text groups, not a single unified panel
- **Optional UI Integration**: Fuel/Tyre/Nitro/Pit are PART of the guaranteed control row when optional UI is present
- **Status Bars**: Below main row at y≈970-1010

**Nitro** is an outlier - positioned far left (x≈550-700), separate from main cluster.

---

### 7. Unknown States (Require Additional Ground Truth)

| Control | Known State(s) | Unknown States Needed |
|---------|----------------|------------------------|
| **Strategy** | BALANCED | Safe, Attack, or other states |
| **Pace** | NEUTRAL | Conserve, Push, or other states |
| **Tyre** | SOFT | Medium, Hard, or other compounds |
| **Fuel** | RICH | Lean, Standard, or other modes |
| **Defend** | **None** (state not visible) | ON, OFF (or whatever states exist) |
| **Nitro** | 0 | 1, 2, 3, max (numeric range) |
| **Pit** | BOX BOX | Other options (Don't Pit, etc.) |

---

### 8. Minimum Additional Ground Truth Required

Based **only** on this screenshot, the minimum additional screenshots needed:

| Priority | Screenshots | Purpose |
|----------|-------------|---------|
| **Critical** | 1: Defend ON, 1: Defend OFF | Defend has **zero visible state** in this screenshot |
| **Critical** | 1: Strategy ≠ BALANCED, 1: Pace ≠ NEUTRAL | Verify other states exist and their text representation |
| **High** | 1: Tyre ≠ SOFT, 1: Fuel ≠ RICH | Verify other compound/mode names |
| **High** | 1: Nitro >0, 1: Pit ≠ BOX BOX | Verify counter/option text changes |
| **Medium** | 1: Optional UI **absent** (same race moment) | Measure layout shift when optional section removed |
| **Medium** | 1: Different resolution (if supported) | Verify coordinate scaling |

**Total minimum: 6-8 additional screenshots** (Defend ×2 + Strategy/Pace/Tyre/Fuel/Nitro/Pit ×1 each + 1 layout-shift reference)

---

### 9. Next Detector Development Step (After Ground Truth Complete)

1. **Text-template extraction**: Crop each control's value region → build exact-match text templates per state
2. **ROI definition**: Fixed relative coordinates per layout (with/without optional UI)
3. **OCR/Template matching**: Exact string match for text values; template match for Defend (icon/toggle)
4. **Layout detector**: Already working (detects optional UI presence via bottom bar analysis)
5. **Output**: Structured observation with text values + confidence

---

*Report generated: 2026-09-16*  
*Source: Single 1920×1080 screenshot, active race, optional UI present*  
*Analysis: OCR + visual inspection + coordinate mapping*  
*Status: Ground truth established for 6/7 controls; Defend state UNKNOWN*