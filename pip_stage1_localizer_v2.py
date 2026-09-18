"""
PIP Stage 1: Improved UI Localizer
Uses OCR to find known label texts for precise localization.
"""
import cv2
import numpy as np
import easyocr
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class LayoutType(Enum):
    WITH_OPTIONAL = "with_optional"
    WITHOUT_OPTIONAL = "without_optional"
    UNKNOWN = "unknown"


@dataclass
class ControlRowLocation:
    y_top: int
    y_bottom: int
    x_left: int
    x_right: int
    layout: LayoutType
    confidence: float
    detection_method: str
    label_positions: dict  # label_text -> (x, y)


class ImprovedUILocalizer:
    """
    Locates race-control row by OCR-detecting known label texts.
    Uses the confirmed ground-truth label texts as anchors.
    """
    
    # Known labels from ground truth (exact text to search for)
    TARGET_LABELS = ["STRATEGY", "PACE", "TYRE", "FUEL", "DEFEND", "PIT", "NITRO"]
    TARGET_VALUES = ["BALANCED", "NEUTRAL", "SOFT", "RICH", "BOX BOX"]
    
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
        self.debug = False
    
    def locate_by_ocr_labels(self, frame: np.ndarray) -> Optional[ControlRowLocation]:
        """
        Use OCR to find the known label texts, then compute control row bounds.
        """
        h, w = frame.shape[:2]
        
        # Search in lower portion where controls are expected
        search_y_start = 700
        search_y_end = 1080
        search_region = frame[search_y_start:search_y_end, 0:w]
        
        if search_region.size == 0:
            return None
        
        # Preprocess for OCR
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Run OCR on enhanced
        try:
            results = self.reader.readtext(enhanced, detail=1, paragraph=False)
        except Exception as e:
            print(f"OCR error: {e}")
            return None
        
        # Filter for target labels
        found_labels = []
        found_values = []
        
        for bbox, text, conf in results:
            if conf < 0.3:
                continue
            text_clean = text.strip().upper()
            
            # Check if it matches a target label
            for target in self.TARGET_LABELS:
                if target in text_clean or text_clean in target:
                    # Convert bbox back to original coordinates
                    # bbox is in 3x upscaled coordinates
                    x_coords = [int(p[0] / 3) for p in bbox]
                    y_coords = [int(p[1] / 3) + 700 for p in bbox]  # add search offset
                    x_center = sum(x_coords) / 4
                    y_center = sum(y_coords) / 4
                    found_labels.append({
                        'text': target,
                        'matched_text': text_clean,
                        'confidence': conf,
                        'x': x_center,
                        'y': y_center,
                        'bbox': (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                    })
                    break
            
            # Check for target values
            for target in self.TARGET_VALUES:
                if target in text_clean or text_clean in target:
                    x_coords = [int(p[0] / 3) for p in bbox]
                    y_coords = [int(p[1] / 3) + 700 for p in bbox]
                    x_center = sum(x_coords) / 4
                    y_center = sum(y_coords) / 4
                    found_values.append({
                        'text': target,
                        'matched_text': text_clean,
                        'confidence': conf,
                        'x': x_center,
                        'y': y_center,
                        'bbox': (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                    })
                    break
        
        if not found_labels:
            return None
        
        # Sort labels by Y then X
        found_labels.sort(key=lambda l: (l['y'], l['x']))
        
        # The label row should have multiple labels at similar Y
        # Group by Y coordinate
        label_rows = {}
        for label in found_labels:
            y_key = round(label['y'] / 10) * 10  # quantize to 10px
            if y_key not in label_rows:
                label_rows[y_key] = []
            label_rows[y_key].append(label)
        
        # Find the row with most labels (the label row)
        best_row_y = max(label_rows.keys(), key=lambda k: len(label_rows[k]))
        label_row = label_rows[best_row_y]
        
        if len(label_row) < 2:
            return None
        
        # Sort by X
        label_row.sort(key=lambda l: l['x'])
        
        # Compute bounds
        xs = [l['x'] for l in label_row]
        ys = [l['y'] for l in label_row]
        
        x_left = int(min(xs) - 50)
        x_right = int(max(xs) + 100)
        y_top = int(min(ys) - 30)
        
        # Find value row below (look for values)
        value_rows = {}
        for val in found_values:
            y_key = round(val['y'] / 10) * 10
            if y_key not in value_rows:
                value_rows[y_key] = []
            value_rows[y_key].append(val)
        
        # Find value row below label row
        value_row_y = None
        for vy in sorted(value_rows.keys()):
            if vy > best_row_y + 10 and vy < best_row_y + 80:
                value_row_y = vy
                break
        
        if value_row_y:
            y_bottom = int(value_row_y + 30)
        else:
            y_bottom = int(best_row_y + 60)
        
        # Build label positions dict
        label_positions = {l['text']: (int(l['x']), int(l['y'])) for l in label_row}
        
        # Detect layout
        layout = self._detect_layout(frame, int(y_bottom))
        
        return ControlRowLocation(
            y_top=int(y_top),
            y_bottom=int(y_bottom),
            x_left=max(0, x_left),
            x_right=min(1920, x_right),
            layout=layout,
            confidence=0.85,
            detection_method="ocr_label_detection",
            label_positions=label_positions
        )
    
    def _detect_layout(self, frame: np.ndarray, control_row_bottom: int) -> LayoutType:
        """Detect optional UI presence"""
        h, w = frame.shape[:2]
        if control_row_bottom >= h - 50:
            return LayoutType.UNKNOWN
        
        check_region = frame[control_row_bottom:min(h, control_row_bottom + 150), 0:w]
        if check_region.size == 0:
            return LayoutType.UNKNOWN
        
        gray = cv2.cvtColor(check_region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        edges = cv2.Canny(thresh, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        text_like = sum(1 for c in contours if 100 < cv2.contourArea(c) < 10000)
        
        if text_like > 8:
            return LayoutType.WITH_OPTIONAL
        return LayoutType.WITHOUT_OPTIONAL
    
    def locate_control_row(self, frame: np.ndarray) -> ControlRowLocation:
        """Main entry point"""
        # Try OCR-based detection
        result = self.locate_by_ocr_labels(frame)
        if result:
            return result
        
        # Fallback
        return ControlRowLocation(
            y_top=900, y_bottom=980, x_left=200, x_right=1720,
            layout=LayoutType.UNKNOWN, confidence=0.1,
            detection_method="fallback", label_positions={}
        )


def test_localizer():
    localizer = ImprovedUILocalizer()
    
    gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
    frame = cv2.imread(gt_path)
    
    if frame is None:
        print("Failed to load ground truth")
        return
    
    print("=== Testing Improved UI Localizer on Ground Truth ===")
    location = localizer.locate_control_row(frame)
    
    print(f"Detected control row:")
    print(f"  y_top: {location.y_top}, y_bottom: {location.y_bottom}")
    print(f"  x_left: {location.x_left}, x_right: {location.x_right}")
    print(f"  layout: {location.layout.value}")
    print(f"  confidence: {location.confidence:.2f}")
    print(f"  method: {location.detection_method}")
    print(f"  labels found: {list(location.label_positions.keys())}")
    for label, pos in location.label_positions.items():
        print(f"    {label}: x={pos[0]}, y={pos[1]}")
    
    expected_y_top, expected_y_bottom = 930, 970
    y_error = abs(location.y_top - expected_y_top)
    print(f"\nExpected y_top={expected_y_top}, got {location.y_top}, error={y_error}px")
    
    # Draw debug
    debug = frame.copy()
    cv2.rectangle(debug, (location.x_left, location.y_top), 
                  (location.x_right, location.y_bottom), (0, 255, 0), 3)
    for label, (lx, ly) in location.label_positions.items():
        cv2.circle(debug, (lx, ly), 5, (255, 0, 0), -1)
        cv2.putText(debug, label, (lx, ly - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    cv2.imwrite('frames/ground_truth/localizer_v2_debug.png', debug)
    print("Saved debug to frames/ground_truth/localizer_v2_debug.png")


if __name__ == "__main__":
    test_localizer()