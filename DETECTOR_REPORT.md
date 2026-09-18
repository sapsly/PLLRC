# PIP Visual Detection Prototype - Technical Report
## Targeted Test: Strategy/Pace/Defend Controls

---

### 1. Detection Evidence

#### Strategy Control
| Frame | Detected | Region | Buttons | State | Confidence | Evidence |
|-------|----------|--------|---------|-------|------------|----------|
| Race 6 t=30s | YES | x=50-300, y=1000-1080 | 3 | ATTACK | 0.90 | Btn 2: 71% green; Btn 1: 64% yellow; Btn 0: 48% white |
| Race 6 t=60s | PARTIAL | x=50-300, y=1000-1080 | 4 | UNKNOWN | 0.00 | 4th spurious button detected; 3 main buttons show green/yellow/white |
| Race 6 t=90s | YES | x=50-300, y=1000-1080 | 3 | ATTACK | 0.90 | Same pattern as t=30s |
| Race 6 t=120s | YES | x=50-300, y=1000-1080 | 3 | ATTACK | 0.90 | Same pattern |
| Race 6 t=150s | YES | x=50-300, y=1000-1080 | 3 | ATTACK | 0.90 | Same pattern |
| Race 6 t=180s | YES | x=50-300, y=1000-1080 | 3 | ATTACK | 0.90 | Same pattern |
| Race 6 t=210s | YES | x=50-300, y=1000-1080 | 3 | ATTACK | 0.90 | Same pattern |
| Race 1 t=30s | YES (diff loc) | x≈50-250, y≈750-900 | 4 | UNKNOWN | 0.00 | 4 buttons: white/white/yellow/yellow - no green |
| Race 1 t=60s | YES (diff loc) | x≈50-250, y≈750-900 | 4 | UNKNOWN | 0.00 | Same as t=30s |
| Race 1 t=90s | YES (diff loc) | x≈50-250, y≈750-900 | 4 | UNKNOWN | 0.00 | Same as t=30s |
| Race 1 t=120s | YES (diff loc) | x≈50-250, y≈750-900 | 4 | UNKNOWN | 0.00 | Same as t=30s |

**Key finding**: Race 6 shows Strategy at y=1000-1080 (bottom) with clear 3-button green/yellow/white pattern indicating ATTACK selected. Race 1 shows 4-button pattern at y=750-900 with NO green - only white/yellow. The y-position DIFFERS by ~150-250px between races with/without optional UI.

#### Pace Control
| Frame | Detected | Region | Buttons | State | Confidence | Evidence |
|-------|----------|--------|---------|-------|------------|----------|
| Race 6 (all) | NO | Hypothesized (710-1210, 950-1060) | 4-8 | UNKNOWN | 0.00 | Region contains 4 buttons: green(44%), blue(40%), white(53%), white(32%) - NOT 3-button pattern |
| Race 1 (all) | NO | Hypothesized | 2 | UNKNOWN | 0.00 | Only 2 small white buttons detected |

**Key finding**: The hypothesized Pace region (bottom-center) in Race 6 is PART OF THE OPTIONAL UI (fuel/tyre/nitro), showing 31% green across full width. Race 1 (no optional UI) has NO green in bottom-center. Pace control NOT located in hypothesized region.

#### Defend Control
| Frame | Detected | Region | Buttons | State | Confidence | Evidence |
|-------|----------|--------|---------|-------|------------|----------|
| Race 6 (all) | NO | Hypothesized (1620-1900, 400-500) | 0-5 | UNKNOWN | 0.00 | Hypothesized region empty; right-lower (y=720-1080) shows 5 red buttons at t=150s |
| Race 1 (all) | NO | Hypothesized | 0 | UNKNOWN | 0.00 | Right strip shows no color, no buttons at any y |

**Key finding**: Defend NOT at hypothesized right-mid location. Race 6 right-lower (y=1000-1080) has red buttons but this appears to be optional UI, not Defend.

---

### 2. False Positives

| Region | Mistaken For | Actual Content |
|--------|--------------|----------------|
| Bottom-center (x=710-1210, y=950-1060) | Pace | Optional UI section - fuel/tyre/nitro controls (31% green, 27 buttons in full bottom) |
| Right-lower (x=1620-1900, y=720-1080) | Defend | Optional UI extension - appears only when optional section present |
| Bottom-left 4th button (Race 6 t=60s) | Strategy extra state | Spurious detection from optional UI bleed |
| Top-center yellow/blue buttons | Strategy/Pace | Menu/UI elements (SHOP, CARDS, GARAGE, LIVE RACE) |

---

### 3. False Negatives

| Control | Frames Missed | Likely Cause |
|---------|---------------|--------------|
| **Pace** | ALL 11 frames | Not in hypothesized region; location unknown |
| **Defend** | ALL 11 frames | Not in hypothesized region; location unknown |
| **Strategy** | Race 6 t=60s (4 buttons instead of 3) | Optional UI pushing into region |
| **Strategy** | Race 1 (all frames) | Wrong y-position for this layout; detector uses fixed coordinates |

---

### 4. Stability Analysis

| Property | Strategy | Pace | Defend |
|----------|----------|------|--------|
| **Coordinates stable?** | ❌ NO - shifts ~150-250px vertically between Race 6 (with optional UI) and Race 1 (without) | N/A - not found | N/A - not found |
| **Button count stable?** | ⚠️ PARTIAL - 3 buttons in Race 6 active racing; 4 buttons when optional UI overlaps (t=60s); 4 buttons in Race 1 | N/A | N/A |
| **Button sizes stable?** | ✅ YES - ~15-21px wide, ~15-19px tall consistently | N/A | N/A |
| **Colors stable?** | ✅ YES - Green (selected), Yellow (neutral?), White (unselected/dim) consistent in Race 6 | N/A | N/A |
| **Selected appearance stable?** | ✅ YES - Attack (rightmost) shows 70%+ green across all Race 6 frames | N/A | N/A |
| **Optional UI causes shift?** | ✅ YES - Race 6 (with optional) has Strategy at y=1000; Race 1 (without) at y≈750-900 | N/A | N/A |

**Critical finding**: The bottom region (y=900-1080) with 30%+ green in Race 6 IS THE OPTIONAL UI. It only exists when optional section is present. Race 1 has ZERO green in bottom 180px.

---

### 5. Visual Characteristics Summary

| Region | Race 6 (with optional) | Race 1 (no optional) |
|--------|------------------------|----------------------|
| **Top (0-150)** | 37 btns, minimal color | 63 btns, minimal color |
| **Upper-mid (150-300)** | 18 btns | 26 btns |
| **Mid (300-450)** | 8 btns | 13 btns |
| **Mid-lower (450-600)** | 37 btns | 24 btns |
| **Lower-mid (600-750)** | 15 btns | 13 btns |
| **Upper-bottom (750-900)** | 9 btns | 20 btns, **3.6% green** |
| **Bottom (900-1080)** | **31% green, 35 btns** | 0.3% green, 40 btns |

**The guaranteed controls are NOT in the bottom 180px** - that's the optional UI.

---

### 6. Recommendation

**NEXT SMALLEST STEP**: 

Search for the **actual guaranteed controls** in the **upper-bottom band (y=750-900)** and **top region (y=0-150)** where:
- Race 1 shows 3.6% green at y=750-900 with 20 buttons (candidate for Strategy/Pace/Defend)
- Both races have dense button-like contours in top region (Race 6: 37, Race 1: 63) with some yellow/blue color

**Specific action**: 
1. Extract crops from y=750-900 band (full width) for both races
2. Look for THREE distinct 3-button groups horizontally separated (Strategy left, Pace center, Defend right)
3. Test if Race 1's y=750-900 green region contains the guaranteed controls
4. Use template matching on the 3-button pattern once a candidate group is visually confirmed

**Do NOT** continue tuning HSV thresholds on the wrong regions. The guaranteed controls are visually distinct from the optional UI and appear at different vertical positions depending on layout.

---

*Report generated: 2026-09-16*  
*Test scope: Visual detection prototype only*  
*Frames tested: 11 (7 from Race 6, 4 from Race 1)*  
*Next action: Search y=750-900 band and top region for 3-button groups*