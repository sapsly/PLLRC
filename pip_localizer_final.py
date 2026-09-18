"""
PIP Stage 1: Refined UI Localizer
Uses OCR-detected label/value positions for accurate localization.
"""
import cv2
import numpy as np
import easyocr
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
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
    label_positions: Dict[str, Tuple[int, int]]
    value_positions: Dict[str, Tuple[int, int]]


class UILocalizer:
    """
    Locates race-control row by OCR-detecting known label/value texts.
    """
    
    TARGET_LABELS = ["STRATEGY", "PACE", "TYRE", "FUEL", "DEFEND", "PIT", "NITRO"]
    TARGET_VALUES = ["BALANCED", "NEUTRAL", "SOFT", "RICH", "BOX BOX", "0"]
    
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def locate_control_row(self, frame: np.ndarray) -> ControlRowLocation:
        h, w = frame.shape[:2]
        
        # Search lower portion
        search_y_start = 650
        search_y_end = 1080
        search_region = frame[search_y_start:search_y_end, 0:w]
        
        if search_region.size == 0:
            return self._fallback()
        
        # Preprocess for OCR
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(up)
        
        # OCR
        try:
            results = self.reader.readtext(enhanced, detail=1, paragraph=False)
        except Exception as e:
            print(f"OCR error: {e}")
            return self._fallback()
        
        # Collect label and value detections
        labels = []
        values = []
        
        for bbox, text, conf in results:
            if conf < 0.3:
                continue
            text_clean = text.strip().upper()
            
            # Convert bbox to original frame coordinates
            x_coords = [int(p[0] / 3) for p in bbox]
            y_coords = [int(p[1] / 3) + 650 for p in bbox]  # search_y_start = 650
            x_center = int(sum(x_coords) / 4)
            y_center = int(sum(y_coords) / 4)
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            text_clean = text.strip().upper()
            
            # Match labels
            for target in ["STRATEGY", "PACE", "TYRE", "FUEL", "DEFEND", "PIT", "NITRO"]:
                if target in text_clean or text_clean in target:
                    labels.append({
                        'text': target, 'x': x_center, 'y': y_center,
                        'x_min': x_min, 'x_max': x_max, 'y_min': y_min, 'y_max': y_max,
                        'conf': conf
                    })
                    break
            
            # Match values
            for target in ["BALANCED", "NEUTRAL", "SOFT", "RICH", "BOX BOX", "0"]:
                if target in text_clean or text_clean in target:
                    values.append({
                        'text': target, 'x': x_center, 'y': y_center,
                        'conf': conf
                    })
                    break
        
        if not labels:
            return self._fallback()
        
        # Group labels by Y coordinate (find the label row)
        labels.sort(key=lambda l: l['y'])
        
        # Find clusters of labels at similar Y
        best_cluster = None
        best_size = 0
        
        for i, label in enumerate(labels):
            cluster = [label]
            for j, other in enumerate(labels):
                if i != j and abs(other['y'] - label['y']) <= 15:
                    cluster.append(other)
            if len(cluster) > best_size:
                best_size = len(cluster)
                best_cluster = cluster
        
        if not best_cluster or len(best_cluster) < 2:
            return self._fallback()
        
        # Compute label row bounds
        cluster = best_cluster
        label_ys = [l['y'] for l in cluster]
        label_xs = [l['x'] for l in cluster]
        label_row_y = int(sum(label_ys) / len(label_ys))
        label_row_x_min = min(l['x_min'] for l in cluster)
        label_row_x_max = max(l['x_max'] for l in cluster)
        
        # Find value row (below label row, similar X span)
        value_row_y = None
        value_candidates = [v for v in values if v['y'] > label_row_y + 5 and v['y'] < label_row_y + 50]
        if value_candidates:
            value_ys = [v['y'] for v in value_candidates]
            value_row_y = int(sum(value_ys) / len(value_ys))
        
        # Compute control row bounds
        y_top = max(0, label_row_y - 30)
        y_bottom = value_row_y + 30 if value_row_y else label_row_y + 60
        x_left = max(0, label_row_x_min - 50)
        x_right = min(1920, label_row_x_max + 100)
        
        # Build position dicts
        label_positions = {l['text']: (l['x'], l['y']) for l in cluster}
        value_positions = {v['text']: (v['x'], v['y']) for v in values}
        
        # Detect layout
        layout = self._detect_layout(frame, y_bottom)
        
        return ControlRowLocation(
            y_top=label_row_y - 30,
            y_bottom=y_bottom,
            x_left=x_left,
            x_right=x_right,
            layout=layout,
            confidence=0.9 if len(cluster) >= 4 else 0.7,
            detection_method="ocr_label_cluster",
            label_positions={l['text']: (l['x'], l['y']) for l in cluster},
            value_positions={v['text']: (v['x'], v['y']) for v in values}
        )
    
    def _detect_layout(self, frame: np.ndarray, control_row_bottom: int) -> LayoutType:
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
    
    def _fallback(self) -> ControlRowLocation:
        return ControlRowLocation(
            y_top=900, y_bottom=980, x_left=200, x_right=1720,
            layout=LayoutType.UNKNOWN, confidence=0.1,
            detection_method="fallback", label_positions={}, value_positions={}
        )


def test_localizer():
    localizer = UILocalizer()
    
    gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
    frame = cv2.imread(gt_path)
    
    if frame is None:
        print("Failed to load ground truth")
        return
    
    print("=== Testing Refined UI Localizer on Ground Truth ===")
    location = localizer.locate_control_row(frame)
    
    print("Detected control row:")
    print("  y_top: {}, y_bottom: {}".format(location.y_top, location.y_bottom))
    print("  x_left: {}, x_right: {}".format(location.x_left, location.x_right))
    print("  layout: {}".format(location.layout.value))
    print("  confidence: {:.2f}".format(location.confidence))
    print("  method: {}".format(location.detection_method))
    print("  labels found: {}".format(list(location.label_positions.keys())))
    for label, pos in location.label_positions.items():
        print("    {}: x={}, y={}".format(label, pos[0], pos[1]))
    print("  values found: {}".format(list(location.value_positions.keys())))
    
    expected_y_top, expected_y_bottom = 860, 890  # Based on actual OCR detections
    y_error = abs(location.y_top - expected_y_top)
    print("\nExpected y_top={}, got {}, error={}px".format(expected_y_top, location.y_top, y_error))
    
    # Draw debug
    debug = frame.copy()
    cv2.rectangle(debug, (location.x_left, location.y_top), 
                  (location.x_right, location.y_bottom), (0, 255, 0), 3)
    for label, (lx, ly) in location.label_positions.items():
        cv2.circle(debug, (lx, ly), 5, (255, 0, 0), -1)
        cv2.putText(debug, label, (lx, ly - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    for val, (vx, vy) in location.value_positions.items():
        cv2.circle(debug, (vx, vy), 5, (0, 255, 255), -1)
    cv2.imwrite('frames/ground_truth/localizer_final_debug.png', debug)
    print("Saved debug to frames/ground_truth/localizer_final_debug.png")


if __name__ == "__main__":
    test_localizer()