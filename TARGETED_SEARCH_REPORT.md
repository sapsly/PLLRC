# PIP Targeted Visual Search - Technical Report
## Locating Strategy/Pace/Defend Controls

---

### 1. Investigation Summary

**Frames tested**: 5 frames from 3 races
- Race 6 (with optional UI): t=90s, t=150s
- Race 1 (without optional UI): t=60s, t=100s  
- Race 5 (without optional UI): t=40s

**Method**: Lightweight contour-based search for 3-button horizontal groups (Strategy, Pace) and 2-button/toggle groups (Defend), with color profiling and cross-frame persistence checking.

---

### 2. Strategy Control

**Status: NOT LOCATED**

| Candidate | Frame | Region | Buttons | Evidence | Verdict |
|-----------|-------|--------|---------|----------|---------|
| Race 1 bottom-left | t=60s, t=100s | x=143-244, y=1039 | 3 | Persistent; red(10%)+yellow(9%)+blue(2%); no green; high value (166) | REJECTED - no green-selected pattern |
| Race 1 upper-mid | t=60s, t=100s | x=754-859, y=206 | 3 | Persistent; consistent 13px height; blue(10-11%) only; no green/red | REJECTED - no selection colors |
| Race 6 upper-mid | t=150s | x=1215-1320, y=205 | 3 | Single frame only; irregular sizes (7,48,40px); dark | REJECTED - inconsistent, not persistent |
| Race 6 bottom | t=90s, t=150s | Multiple x, y=1034-1041 | 3 | Part of dense optional UI grid (31% green); not persistent at same x | REJECTED - optional UI |

**Layout shift evidence**: 
- Race 1 (no optional): 3-btn groups at y=1039-1043 (bottom 40px)
- Race 6 (with optional): NO 3-btn groups in y=700-900 (above optional UI); bottom is optional UI
- **Conclusion**: If Strategy is a 3-button group, it is ABSENT from Race 6 middle region when optional UI is present. The bottom groups in Race 1 are a dense grid, not isolated Strategy/Pace controls.

---

### 3. Pace Control

**Status: NOT LOCATED**

| Candidate | Frame | Region | Buttons | Evidence | Verdict |
|-----------|-------|--------|---------|----------|---------|
| Race 1 bottom-center | t=60s, t=100s | x=824-925, y=1041 | 3 | Persistent; white(6%)+blue(1%); no green/red/yellow | REJECTED - no selection colors |
| Race 1 bottom-left | t=60s only | x=64-165, y=1040 | 3 | NOT persistent (absent at t=100s); white only | REJECTED - not persistent |
| Race 6 bottom | t=90s, t=150s | x=854, y=1050 | 2-btn only | Part of optional UI; shows green but inconsistent button count | REJECTED - optional UI, wrong button count |

**Layout shift evidence**: 
- Same as Strategy - no 3-button groups found in Race 6 middle region
- Race 1 bottom groups are a dense grid, not isolated Pace control

---

### 4. Defend Control

**Status: NOT LOCATED**

| Candidate | Frame | Region | Buttons | Evidence | Verdict |
|-----------|-------|--------|---------|----------|---------|
| Race 1 bottom | t=60s, t=100s | 22 persistent 2-btn groups across bottom | 2 | Too many candidates (22 persistent); dense grid | REJECTED - not unique |
| Race 6 right vertical | t=150s | x=1620, y=618-693 | 3 | Single frame; vertical stack; heights 18,16,14px; dark | REJECTED - 3 buttons not 2, not persistent |
| Race 6 right lower | t=150s | x=1620, y=720-1080 | Multiple 2-btn | Part of optional UI extension | REJECTED - optional UI |

**Layout shift evidence**: 
- No consistent 2-button toggle found in either layout
- Race 6 right-side vertical group at t=150s only - not stable

---

### 5. False Positives Rejected

| Region | Mistaken For | Actual Content | Why Rejected |
|--------|--------------|----------------|--------------|
| Race 1 bottom (y=1034-1043) | Strategy/Pace/Defend | Dense grid of 20×20px buttons (~40+ persistent groups) | Too many groups; no green-selected pattern; grid not 3 distinct controls |
| Race 6 bottom (y=900-1080) | Strategy/Pace/Defend | Optional UI section (fuel/tyre/nitro) | 31% green; 35+ buttons; only present with optional modifier |
| Race 6 upper-mid (t=150s) | Strategy | Irregular 3-btn group at x=1215 | Inconsistent sizes (7,48,40px); single frame; dark |
| Race 1 upper-mid (y=206) | Strategy/Pace | 3 blue buttons at x=754-859 | No selection colors (green/red/yellow); blue only |
| Race 6 right vertical (t=150s) | Defend | 3-btn vertical stack at x=1620 | 3 buttons not 2; single frame; not persistent |

---

### 6. Stability Analysis

| Property | Finding |
|----------|---------|
| **Coordinates stable across time?** | Race 1 bottom grid: YES (persistent at same x across t=60s/t=100s). Race 6: NO 3-btn groups in middle region at any time. |
| **Button sizes stable?** | Race 1 bottom: YES (~20×20px consistent). Race 6 optional UI: YES. |
| **Colors stable?** | Race 1 bottom: YES (white/bright dominant, no green). Race 6 optional UI: YES (green dominant). |
| **Selected appearance stable?** | NO green-selected pattern found in ANY persistent group. |
| **Optional UI causes position change?** | YES - Race 1 bottom has 3-btn groups; Race 6 middle has NONE. Controls either move, hide, or change form when optional UI present. |

---

### 7. Critical Finding

**The guaranteed in-race controls (Strategy 3-state, Pace 3-state, Defend 2-state) are NOT visibly present as 3-button horizontal groups or 2-button toggles in the tested footage.**

Evidence:
1. **Race 1 (no optional UI)**: Bottom 40px contains a dense persistent grid of ~20×20px buttons (40+ groups). None show the expected green-selected / red-unselected / yellow-neutral color pattern for 3-state controls.
2. **Race 6 (with optional UI)**: The bottom 180px is the optional UI (fuel/tyre/nitro). The region above it (y=700-900) contains ZERO 3-button horizontal groups. The guaranteed controls are absent from their expected location.
3. **Race 5 (no optional UI)**: Same bottom grid pattern as Race 1.
3. **No 2-button toggle** uniquely identifiable as Defend in either layout.

---

### 8. Next Smallest Step

**RECOMMENDATION**: Obtain ground-truth reference frames showing the guaranteed controls in known states.

**Specific action**: 
1. Capture or obtain screenshots from the game directly (not video) showing:
   - Strategy set to Safe / Neutral / Attack
   - Pace set to Conserve / Neutral / Push  
   - Defend set to On / Off
2. At native resolution, without video compression artifacts
3. In both UI layouts (optional section present / absent)

**Reason**: The video footage either (a) doesn't show the controls clearly due to compression/resolution, (b) the controls use a visual representation not detectable as 3-button groups (icons, text, radial menus, pie charts), or (c) the specific race configurations in the footage don't display the controls. Without ground truth, we cannot distinguish the controls from the dense button grid or optional UI.

**Do not**: Continue tuning HSV thresholds or contour parameters on the current footage. The structural search has been exhaustive for the 3-button/2-button hypothesis.

---

*Report generated: 2026-09-16*  
*Investigation: Targeted visual search (5 frames, 3 races)*  
*Scope: Locate Strategy/Pace/Defend only*  
*Next action: Obtain ground-truth reference images*