# PIP Ground-Truth Acquisition Specification

---

## 1. What Is Now Known

| Finding | Evidence |
|---------|----------|
| The three guaranteed in-race controls (Strategy, Pace, Defend) are **not reliably detectable** in the supplied 1080p race videos | 5 targeted visual search experiments across 3 races (1, 5, 6), 11 frames, exhaustive 3-button/2-button group search |
| The bottom 180px (y=900-1080) in Race 6 is the **optional UI** (fuel/tyre/nitro), not the guaranteed controls | 31% green pixels, 35+ button-like contours, only present when optional modifier active |
| Race 1 (no optional UI) has a dense persistent button grid at y=1034-1043 (40+ 3-btn groups, 22+ 2-btn groups) | Persistent across t=60s/t=100s; white/bright dominant; **zero green** |
| The guaranteed controls either: (a) don't appear in these race configurations, (b) use non-button visual representation, (c) are below video compression/quality threshold, or (d) are in an unsearched location | No 3-state or 2-state control found matching expected patterns |
| Layout shifts when optional UI appears: guaranteed controls absent from y=700-900 in Race 6 | Zero 3-button groups in Race 6 middle region vs multiple in Race 1 |

**No false assumption made**: We did not force detections. UNKNOWN is correctly reported.

---

## 2. What Remains Unknown

| Unknown | Impact |
|---------|--------|
| **Visual appearance** of Strategy (Safe/Neutral/Attack) | Cannot build detector |
| **Visual appearance** of Pace (Conserve/Neutral/Push) | Cannot build detector |
| **Visual appearance** of Defend (On/Off) | Cannot build detector |
| Whether controls use **buttons, icons, text, color bars, radial indicators, or HUD overlays** | Determines detection method |
| Whether controls **change representation** between optional UI layouts | Determines if single or multi-template detector needed |
| **Exact screen coordinates** in native resolution | Required for ROI extraction |
| Whether **controller/key hints** (LB/RB, L1/R1) are present near controls | Could aid localization |

---

## 3. Ground-Truth References Required

### Minimum Set (8 screenshots)

| # | Control | State | Layout | Description |
|---|---------|-------|--------|-------------|
| 1 | Strategy | Safe | Optional UI **absent** | Native 1920×1080, active race |
| 2 | Strategy | Neutral | Optional UI **absent** | Native 1920×1080, active race |
| 3 | Strategy | Attack | Optional UI **absent** | Native 1920×1080, active race |
| 4 | Pace | Conserve | Optional UI **absent** | Native 1920×1080, active race |
| 5 | Pace | Neutral | Optional UI **absent** | Native 1920×1080, active race |
| 6 | Pace | Push | Optional UI **absent** | Native 1920×1080, active race |
| 7 | Defend | On | Optional UI **absent** | Native 1920×1080, active race |
| 8 | Defend | Off | Optional UI **absent** | Native 1920×1080, active race |

### Recommended Additional (4 screenshots) - for layout adaptation

| # | Control | State | Layout | Description |
|---|---------|-------|--------|-------------|
| 9 | Strategy | Any (e.g., Neutral) | Optional UI **present** | Native 1920×1080, active race |
| 10 | Pace | Any (e.g., Neutral) | Optional UI **present** | Native 1920×1080, active race |
| 11 | Defend | Any (e.g., On) | Optional UI **present** | Native 1920×1080, active race |
| 12 | Full frame | Any | Optional UI **present** | Full 1920×1080 to measure layout shift |

**Total minimum: 8 screenshots** (all optional-UI-absent states)  
**Total recommended: 12 screenshots** (includes layout-shift measurement)

---

## 4. Acquisition Requirements

| Requirement | Specification |
|-------------|---------------|
| **Resolution** | Native 1920×1080 (no upscaling/downscaling) |
| **Source** | Direct game capture (Win+Alt+PrntScrn, OBS, NVIDIA ShadowPlay, or in-game photo mode) - **NOT video frame extraction** |
| **Context** | Active race session (not lobby, not pre-race, not post-race, not attribute screen) |
| **Format** | PNG (lossless) or high-quality JPEG (>90%) |
| **Naming** | `control_state_layout.png` e.g., `strategy_safe_nooptional.png` |
| **UI State** | Each screenshot must show the control in the specified state (user must manually set each state in-game) |

### How to Capture (User Instructions)

1. Start a race with **optional modifiers OFF** (standard race)
2. During active racing, cycle **Strategy** to Safe → capture → Neutral → capture → Attack → capture
3. Cycle **Pace** to Conserve → capture → Neutral → capture → Push → capture  
4. Cycle **Defend** to On → capture → Off → capture
5. (Optional) Start a race with **optional modifiers ON** (fuel/tyre/nitro)
6. Capture one frame showing all three controls in any state (for layout shift measurement)

---

## 5. Next Detector Development Step (After Ground Truth)

### Step 1: Template/Feature Extraction (1-2 days)
```python
# For each ground-truth screenshot:
1. Crop the control region manually (or use annotation tool)
2. Extract visual features:
   - If buttons: HSV color templates for each state
   - If icons: ORB/SIFT keypoints or CNN embedding
   - If text: OCR character templates
   - If color bars: HSV range profiles
3. Measure intra-state variance, inter-state separation
```

### Step 2: ROI Localization (1 day)
```python
# Build layout-aware ROI finder:
1. Detect optional UI presence (existing layout detector works)
2. Define anchor points (e.g., "below lap counter", "left of speed", "above optional UI")
3. Compute relative ROI offsets for each control in both layouts
```

### Step 3: State Classifier (1 day)
```python
# Per-control classifier:
1. Extract ROI from live frame
2. Compare to ground-truth templates (template matching / feature distance / color histogram)
3. Output: state enum + confidence + UNKNOWN if below threshold
4. Temporal smoothing (3-frame majority vote)
```

### Step 4: Integration & Testing (1 day)
```python
# Pipeline:
Frame → LayoutDetector → ROIExtractor → StateClassifiers → StructuredObservation
```

---

## 6. Stop Criteria for This Phase

**STOP HERE.** Do not proceed to implementation until ground-truth screenshots (minimum 8, recommended 12) are provided by the user.

The investigation has been exhaustive within the constraints of the supplied footage. The next phase requires actual visual reference material from the game itself.

---

*Specification generated: 2026-09-16*  
*Investigation complete: 5 experiments, 3 races, 11 frames, exhaustive structural search*  
*Status: AWAITING GROUND TRUTH*