# PIP OCR/Perception System - Technical Report
## Pit Lane Legends Ranked Racing - Initial Investigation

---

### 1. Current Implementation Status

**No production OCR system exists yet.** The investigation phase has been completed with the following components developed for testing:

- **LayoutDetector**: Heuristic-based layout classification (STANDARD vs WITH_OPTIONAL)
- **TextRecognizer**: EasyOCR wrapper with multi-preprocessing (CLAHE, Otsu, adaptive threshold)
- **UIParser**: Keyword-based parsing for Strategy/Pace/Defend states
- **PIPOCRSystem**: Main pipeline integrating layout detection → region extraction → OCR → parsing

All components are in `pip_ocr.py` and `pip_ocr_fast.py` (testing variants).

---

### 2. OCR Pipeline Used

| Stage | Method | Details |
|-------|--------|---------|
| **Preprocessing** | CLAHE + Otsu threshold | 2x-4x upscale → CLAHE (clipLimit=2.0) → Otsu binarization |
| **OCR Engine** | EasyOCR (CPU) | English model, paragraph=False, detail=1 |
| **Layout Detection** | Edge/contour analysis | Canny edges → contour detection → panel counting in middle region |
| **Region Extraction** | Fixed relative coordinates | 15 predefined regions (top/mid/bottom, left/center/right) |
| **Post-processing** | Keyword matching | Exact/substring match against known state keywords |

---

### 3. UI Layout Detection - How It Works

The detector classifies each frame into one of three layouts:

| Layout | Criteria | Indicates |
|--------|----------|-----------|
| `STANDARD` | Top region has text (>1000 white pixels), middle has <2 panels | Normal race UI, optional section absent |
| `WITH_OPTIONAL` | Top region has text AND middle has ≥2 rectangular panels | Optional section present (fuel, tyres, nitro, pit options) |
| `UNKNOWN` | Neither condition met | Menu, pre-race, or post-race screens |

**Tested on Race 6 (227s):** Detected layout changes at t≈60s and t≈150s correlating with visual changes.

---

### 4. What Was Tested

| Video | Duration | Frames Tested | Key Timestamps |
|-------|----------|---------------|----------------|
| Race_001_06-09-2026 | 144.5s | 29 (5s interval) + 10 (change points) | t=0, 25.7, 39.5, 100s |
| Race_005_07-09-2026 | 78.4s | 8 (10s interval) | t=0, 45.9s |
| Race_006_07-09-2026 | 227.0s | 232 (1s) + 20 (10s) + 8 (key moments) | t=10, 20, 30, 60, 67.7, 90, 120, 149.4, 150, 151.4, 180, 210, 221s |
| Race_007_07-09-2026 | 193.9s | 20 (10s) | t=0, 65.8, 191.5s |

**Total OCR calls:** ~500+ region scans across 4 races

---

### 5. Test Results - Key Findings

#### 5.1 Target Controls NOT Found as Readable Text

The three guaranteed in-race controls (**Strategy**, **Pace**, **Defend**) were **not reliably detected as text** by OCR in any tested frame.

| Control | Expected Values | OCR Detection |
|---------|----------------|---------------|
| Strategy | Safe / Neutral / Attack | ❌ Not found |
| Pace | Conserve / Neutral / Push | ❌ Not found (but "PACE" label seen at t=60s in attribute screen) |
| Defend | On / Off | ❌ Not found |

#### 5.2 What WAS Detected (Non-Target UI)

| Screen/Region | Text Found | Context |
|---------------|------------|---------|
| Top center (all races) | "NDS", "SHOP", "CARDS", "GARAGE", "RANKED", "LIVE RACE", "LAP X/Y" | Persistent menu/header bar - NOT race controls |
| Mid center (t=10-20s) | "FORCED PIT", fuel info | Pre-race modifier screen |
| Mid center (t=60s) | "DRIVER", "0 POINTS LEFT", "PACE", "FOCUS", "CONTROL", "RACECRAFT" | **Attribute screen (Category C)** - NOT in-race controls |
| Mid center (t=30s) | "HOSPITALITY SUITE", "APPEARANCE FEE", "COMEBACK SPONSOR" | Modifier description screen |
| Bottom regions | "Hold My Hand", music player UI | Overlay/media player |
| Right side | "Switch to video" | Streaming overlay |

#### 5.3 Visual Characteristics of Candidate Regions

| Region | Color Signature | Contour Features | Hypothesis |
|--------|----------------|------------------|------------|
| **Bottom row (L/C/R)** | **~30% GREEN** pixels | 3-5 button-like contours (20x20px) | **Primary candidate for Strategy/Pace** - green = active state |
| **Right vertical (mid/lower)** | **3-10% RED** pixels | 1-2 button-like contours | **Candidate for Defend** - red = Off state |
| **Top center** | Minimal color | 2 square contours (27x27px) | Menu buttons, not race controls |

---

### 6. Known Failure Cases

| Issue | Description | Impact |
|-------|-------------|--------|
| **Controls not text-based** | Strategy/Pace/Defend appear to be icon/color indicators, not OCR-readable text | OCR pipeline cannot detect current state |
| **Layout shifts unhandled** | When optional section appears/disappears, control positions shift vertically | Fixed relative coordinates fail |
| **Confusion with Category C screens** | Attribute screens contain "PACE", "FOCUS" labels but are not the in-race Pace control | False positives in keyword parser |
| **Music/stream overlays** | "Hold My Hand", "Switch to video" appear in bottom/right regions | Noise in target regions |
| **OCR too slow for real-time** | 3-5 seconds per frame on CPU | Not viable for live processing |

---

### 7. Specific Improvements Needed Next

| Priority | Improvement | Rationale |
|----------|-------------|-----------|
| **1. CRITICAL** | **Visual template matching for icon/color states** | Controls are likely colored icons (green/red dots, arrows, shields), not text. Need HSV-based state classification. |
| **2. HIGH** | **Dynamic region tracking** | Replace fixed coordinates with anchor-based positioning (e.g., "below lap counter", "right of speed") |
| **3. HIGH** | **Separate Category A/B/C classifiers** | Explicitly detect and exclude pre-race, attribute, and overlay screens before parsing controls |
| **4. MEDIUM** | **GPU acceleration / ONNX runtime** | EasyOCR on CPU is too slow; need <100ms/frame for temporal consistency |
| **5. MEDIUM** | **Temporal smoothing** | State should be consistent across frames; implement Kalman filter or majority voting over N frames |

---

### 8. Additional Footage/Data Needed

| Need | Reason |
|------|--------|
| **Close-up screenshots of Strategy/Pace/Defend controls** | Current 1080p footage too low-res for small icons; need native resolution captures |
| **Frames with each control in EACH state** | Safe/Neutral/Attack, Conserve/Neutral/Push, On/Off - need visual reference for template matching |
| **Transition footage (optional section appear/disappear)** | To measure exact pixel shift and build dynamic layout adaptation |
| **Different screen resolutions / aspect ratios** | Current test only 1920x1080; need 1440p, 4K, ultrawide coverage |
| **Clean frames without music/stream overlays** | "Hold My Hand" and "Switch to video" obscure bottom/right regions |

---

### 9. Coordinate Summary for Next Phase

Based on visual analysis of Race 6 frame at t=150s (LIVE RACE), the most promising regions for **icon/color-based detection**:

| Control | Approx Region (1920x1080) | Detection Method |
|---------|---------------------------|------------------|
| **Strategy** | Bottom-left: x≈50-300, y≈950-1060 | HSV green/red/yellow detection on 3 button slots |
| **Pace** | Bottom-center: x≈710-1210, y≈950-1060 | HSV green/red/yellow detection on 3 button slots |
| **Defend** | Right-mid: x≈1620-1900, y≈400-500 | HSV green/red detection on 2-state toggle |

**Layout shift estimate:** When optional section present, bottom controls move UP ~80-100px.

---

### 10. Recommended Next Smallest Step

**Do not build more OCR.** Instead:

1. **Create HSV color templates** for the 3-button groups in bottom row (Strategy/Pace) and 2-state toggle on right (Defend)
2. **Test on 5 frames** from Race 6 (t=10, 60, 150, 180, 210s) + 2 frames from Race 1 (t=30, 100s)
3. **Measure accuracy** of color-based state detection vs ground truth
4. **Only then** integrate with layout detector and build structured observation output

This follows the CODE → TEST → REPORT → IMPROVE loop with a **targeted, verifiable step** that addresses the core finding: **the controls are visual indicators, not text.**

---

*Report generated: 2026-09-15*  
*Investigation scope: OCR/Perception only (PIP Stage 1)*  
*Next action: Color/template-based detection prototype*