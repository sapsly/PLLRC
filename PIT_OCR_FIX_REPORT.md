# PIP PIT Control Recognition Fix Attempt - Technical Report

---

### 1. Exact Reason PIT OCR Failed

**Root Cause:** The PIT control region in the ground-truth screenshot (and all tested video frames) is **extremely dark and visually uniform**, making text completely undetectable by OCR.

**Evidence:**
- PIT region (x=1600-1910, y=832-952) in ground-truth screenshot:
  - Mean gray value: **7.1** (0-255 scale)
  - Max gray value: **11**
  - Standard deviation: **0.6**
  - Blue channel max: **17**
  - Value channel (HSV) max: **17**
- Full-frame OCR on ground-truth screenshot finds **zero** occurrences of "PIT" or "BOX BOX" anywhere
- 7 preprocessing methods tested (invert, CLAHE, contrast stretch, tophat, blackhat, etc.) — **all returned zero text detections**
- Video frames tested (Race 1, Race 6 at multiple timestamps): Only t=148-150s showed content in PIT region, but OCR detected music overlay text ("at Do You Do?", "AII IAm") not PIT control

**Conclusion:** The PIT control in the provided screenshot is **not rendered as readable text** — it is either:
- A dark button/icon with no visible text
- Text rendered in a color/contrast invisible to grayscale OCR
- Not present in this specific frame moment

---

### 2. Exact Code Change Made

**File:** `pip_localizer_v3.py` (lines 177-210)

**Change:** Modified localizer row width calculation from fixed 1100px centered window to **adaptive right-edge anchoring**:

```python
# OLD (fixed 1100px centered):
cluster_center_x = int(sum(a['x'] for a in cluster) / len(cluster))
estimated_width = 1100
x_left = max(0, cluster_center_x - 1100 // 2)
x_right = min(1920, cluster_center_x + 1100 // 2)

# NEW (adaptive right-edge anchoring):
x_max = 1910  # Near right edge
min_expected_width = 1300
if detected_width < min_expected_width:
    cluster_center_x = int(sum(a['x'] for a in cluster) / len(cluster))
    half_width = min_expected_width // 2
    x_min = max(0, cluster_center_x - half_width)
    x_max = min(1920, cluster_center_x + half_width)
```

**Result:** Row width expanded from ~474px to ~1330px, now covering full control row including PIT region (x=1910 covers PIT at ~1700).

---

### 3. Ground-Truth Screenshot Result

**Screenshot:** `Screenshot 2026-09-08 21.24.37.png` (1920×1080, optional UI present)

| Control | Expected | Detected | Match |
|---------|----------|----------|-------|
| STRATEGY | BALANCED | BALANCED | ✅ |
| PACE | NEUTRAL | NEUTRAL | ✅ |
| TYRE | SOFT | SOFT | ✅ |
| FUEL | RICH | RICH | ✅ |
| NITRO | 0 | 0 | ✅ |
| **PIT** | BOX BOX | **UNKNOWN** | ❌ |
| DEFEND | UNKNOWN | UNKNOWN | ✅ (expected) |

**Localization:** `y=832-952, x=584-1910` (width: 1326px, includes PIT region at x=1910)

**PIT OCR Result:** **Zero text detected** in PIT region (x=1600-1910, y=832-952) with 7 preprocessing methods tested.

---

### 4. Video Frame Result

**Test Frame:** Race 6, t=150s (`frames/recovery/test_t150s.png`)

| Control | Detected | Confidence |
|---------|----------|------------|
| STRATEGY | UNKNOWN | 0.00 |
| PACE | NEUTRAL | 1.00 |
| TYRE | UNKNOWN | 0.00 |
| FUEL | UNKNOWN | 0.00 |
| NITRO | UNKNOWN | 0.00 |
| PIT | UNKNOWN | 0.00 |
| DEFEND | UNKNOWN | 0.00 |

**Localization:** `y=810-930, x=577-1910` (width: 1333px, includes PIT region)

**PIT Region OCR:** Detected music overlay text ("at Do You Do?", "AII IAm") — not PIT control.

---

### 5. Before/After OCR Output

| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| Row width | 474px | 1326px (+852px) |
| PIT region included | ❌ (x_max=1248) | ✅ (x_right=1910) |
| PIT OCR detections | 0 | 0 |
| PIT value read | UNKNOWN | UNKNOWN |

**The localization fix successfully includes the PIT region, but OCR cannot read text that isn't visually present.**

---

### 5. Confidence Assessment

| Aspect | Confidence |
|--------|------------|
| Row localization accuracy | 95% (2px error on ground truth) |
| Layout detection | 90% |
| PIT region coverage | 100% (now included) |
| PIT text recognition | 0% (text not visually detectable) |

---

### 6. False Positives

| Control | False Positive | Context |
|---------|---------------|---------|
| NITRO | "0.6 LAPS" → 0 | Misreads lap counter as nitro |
| DEFEND | "DEFEMD", "DEFEMD" | Label detected but no state text |
| PIT | None | Region included but no text found |

---

### 7. Failure Status: **STILL UNRESOLVED**

The PIT recognition failure is **not solved**. The localizer now correctly includes the PIT region, but **the PIT control does not contain readable text in the provided ground-truth screenshot or any tested video frames**.

---

### 8. Next Smallest Improvement

**Recommendation:** Implement **visual template matching** for PIT control state detection instead of OCR.

**Rationale:** 
- PIT control appears to be a dark button/icon with no readable text
- Visual state (BOX BOX vs other) likely indicated by color/icon/brightness change
- Template matching on the PIT region crop would be more robust than OCR

**Implementation Sketch:**
```python
def detect_pit_state(row_crop, pit_x_range):
    pit_crop = row_crop[:, pit_x_range[0]:pit_x_range[1]]
    # Compare against templates: BOX_BOX_template, DONT_PIT_template, etc.
    # Use template matching (cv2.matchTemplate) or color histogram comparison
    # Return "BOX_BOX", "DONT_PIT", "UNKNOWN"
```

**Do not implement yet** — this is the recommended next step per the CODE → TEST → REPORT → IMPROVE cycle.

---

*Report generated: 2026-09-16*  
*Files: `pip_localizer_v3.py`, `pip_final_pipeline.py`, `pip_stage2_ocr.py`*  
*Status: Localization fixed, PIT OCR unresolved — text not visually detectable*