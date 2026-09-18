# PIP Perception/OCR System - Final Technical Report
## Pit Lane Legends Race Companion (PLLRC)

---

### 1. Current Implementation

The PIP (Perception/ML Component) is a two-stage pipeline:

**Stage 1 — UI Localizer (`pip_localizer_v3.py`)**
- Locates the race-control row in 1920×1080 frames using visual structure detection
- Uses OCR to detect known label texts (STRATEGY, PACE, TYRE, FUEL, DEFEND, PIT, NITRO) and value texts (BALANCED, NEUTRAL, ATTACK, CONSERVE, PUSH, SOFT, MEDIUM, HARD, RICH, STANDARD, LEAN, 0-5, BOX BOX)
- Finds the densest horizontal cluster of text anchors to identify the control row
- Estimates row bounds from the anchor cluster center
- Detects layout type (WITH_OPTIONAL / WITHOUT_OPTIONAL) by checking for optional UI elements below the control row
- No hardcoded coordinates — uses visual detection only

**Stage 2 — OCR Reader (`pip_final_pipeline.py`)**
- Extracts the located row region and runs OCR with multiple preprocessing (CLAHE + Otsu threshold)
- Matches expected controls to OCR results using flexible text matching
- Normalizes OCR errors (e.g., "ANCED" → BALANCED, "NEUITRAL" → NEUTRAL, "0.6 LAPS" → 0)
- Returns structured observations with confidence scores

**Key Files:**
- `pip_localizer_v3.py` — Stage 1 localizer
- `pip_stage2_ocr.py` — Stage 2 OCR reader (integrated into final pipeline)
- `pip_final_pipeline.py` — Combined pipeline with test harness
- `pip_localizer_v3.py` — Localizer module
- `pip_stage2_ocr.py` — OCR reader module

---

### 2. OCR Pipeline Used

| Stage | Method | Details |
|-------|--------|---------|
| **Preprocessing** | CLAHE + 3× upscale + Otsu threshold | CLAHE clipLimit=2.0, 3× bicubic upscale, Otsu binarization |
| **OCR Engine** | EasyOCR (CPU) | English model, paragraph=False, detail=1 |
| **Post-processing** | Multi-pass text matching | Exact → partial word → prefix → reverse → fuzzy matching |
| **Fuzzy rules** | 9 specific error corrections | BALANCED (ANCED), NEUTRAL (NEUITRAL), NEUTRAL (NEUT), 0 (0.6 LAPS), BOX BOX (double BOX), PIT (PIT+BOX) |

---

### 3. How UI Layout Detection Works

The localizer detects layout by:
1. Finding all label/value text anchors in lower frame (y=600-1080)
2. Clustering anchors by Y coordinate (≤20px vertical tolerance)
3. Selecting the densest horizontal cluster as the control row
4. Checking region below row (150px) for optional UI density (>8 text-like contours = WITH_OPTIONAL)

**Output:** `LayoutType.WITH_OPTIONAL` or `LayoutType.WITHOUT_OPTIONAL`

---

### 4. What Was Tested

| Test | Description | Result |
|------|-------------|--------|
| **Ground truth screenshot** | 1920×1080, active race, optional UI present | ✅ 5/6 controls correct (STRATEGY=BALANCED, PACE=NEUTRAL, TYRE=SOFT, FUEL=RICH, NITRO=0) |
| **Race 6 t=90s** | Video frame, optional UI absent | ⚠️ Only PACE=NEUTRAL detected |
| **Race 6 t=150s** | Video frame, optional UI present, music overlay | ❌ Only PACE=NEUTRAL detected |

---

### 5. Test Results

**Ground Truth (Screenshot 2026-09-08 21.24.37.png):**
| Control | Expected | Detected | Confidence | Match |
|---------|----------|----------|------------|-------|
| STRATEGY | BALANCED | BALANCED | 1.00 | ✅ |
| PACE | NEUTRAL | NEUTRAL | 0.94 | ✅ |
| TYRE | SOFT | SOFT | 0.98 | ✅ |
| FUEL | RICH | RICH | 0.98 | ✅ |
| NITRO | 0 | 0 | 0.78 | ✅ |
| PIT | BOX BOX | UNKNOWN | 0.00 | ❌ |
| DEFEND | UNKNOWN | UNKNOWN | 0.00 | ✅ (expected) |

**Video Frames (Race 6):**
| Frame | Layout | Controls Detected |
|-------|--------|-------------------|
| t=90s | WITHOUT_OPTIONAL | PACE=NEUTRAL only |
| t=150s | WITH_OPTIONAL | PACE=NEUTRAL only |

---

### 6. Known Failure Cases

| Failure | Cause | Impact |
|---------|-------|--------|
| **PIT not detected** | "BOX BOX" not in OCR output on ground truth; right-side region outside detected row | PIT always UNKNOWN |
| **DEFEND state unknown** | No state text visible in any frame; label detected but no value | DEFEND correctly returns UNKNOWN |
| **Race 6 t=90s** | Only PACE detected; STRATEGY/TYRE/FUEL/NITRO/PIT missing | Localizer finds row but OCR misses most values |
| **Race 6 t=150s** | Music overlay ("Take Me Home") interferes; only PACE detected | Overlay text contaminates OCR |
| **Video frames generally** | Much lower OCR quality than ground truth screenshot | Compression artifacts, motion blur, lower contrast |

---

### 7. Specific Improvements Needed

| Priority | Improvement | Rationale |
|----------|-------------|-----------|
| **1. PIT detection** | Expand localizer x-range rightward; add PIT-specific fuzzy matching for "BOX" | PIT consistently missed; right-side of row not fully covered |
| **2. Video frame robustness** | Temporal smoothing (3-frame majority vote); adaptive thresholding | Video frames have 3-5× more OCR errors than static screenshot |
| **3. DEFEND state** | Visual toggle detection (color/icon) in addition to text | DEFEND has no text state in any observed frame |
| **4. Localizer robustness** | Multi-scale anchor detection; fallback to contour-based row detection | Fails on frames with music overlays or low contrast |
| **5. Performance** | GPU acceleration / ONNX runtime | 3-5s/frame on CPU too slow for real-time |

---

### 8. Additional Data Needed for Testing

| Need | Reason |
|------|--------|
| **Clean video frames** (no music overlay) | Current Race 6/7/8/14/15/16 have "Take Me Home" / "Switch to video" overlays |
| **PIT state variations** | Need frames with "DONT PIT" / other pit states |
| **DEFEND ON/OFF visual states** | Need frames where DEFEND shows ON/OFF visually (icon/color) |
| **Optional UI absent frames with all controls visible** | Race 6 t=90s missing most controls |
| **Different resolutions** | Only 1920×1080 tested |

---

### 9. Next Steps (When Resuming)

1. **Fix PIT detection** — Expand localizer x-range to 1920; add right-side anchor detection
2. **Add DEFEND visual detection** — HSV color analysis for ON/OFF toggle in DEFEND region
3. **Implement temporal smoothing** — 3-frame sliding window majority vote
4. **Test on all 8 videos** — Systematic evaluation across all surviving footage
5. **Performance optimization** — EasyOCR → ONNX Runtime or GPU

---

*Report generated: 2026-09-16*  
*Scope: PIP Stage 1 — OCR/Perception only*  
*Status: Core pipeline functional on ground truth; video frame robustness needs improvement*  
*Codebase: `pip_localizer_v3.py`, `pip_stage2_ocr.py`, `pip_final_pipeline.py`*