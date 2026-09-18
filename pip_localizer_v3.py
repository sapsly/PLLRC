"""
PIP Stage 1: Improved UI Localizer
Uses both label AND value texts as anchors for robust localization.
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
    Locates race-control row by OCR-detecting known label AND value texts.
    """
    
    # Known labels from ground truth
    TARGET_LABELS = ["STRATEGY", "PACE", "TYRE", "FUEL", "DEFEND", "PIT", "NITRO"]
    
    # Known values from ground truth and observed states
    TARGET_VALUES = [
        "BALANCED", "ATTACK", "SAFE",  # Strategy states
        "NEUTRAL", "CONSERVE", "PUSH",  # Pace states
        "SOFT", "MEDIUM", "HARD",  # Tyre compounds
        "RICH", "STANDARD", "LEAN",  # Fuel modes
        "0", "1", "2", "3", "4", "5",  # Nitro counter
        "BOX BOX", "DONT PIT",  # Pit options
    ]
    
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def locate_control_row(self, frame: np.ndarray) -> ControlRowLocation:
        h, w = frame.shape[:2]
        
        # Search lower portion - expanded range
        search_y_start = 600
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
            if conf < 0.25:
                continue
            text_clean = text.strip().upper()
            if len(text_clean) < 2:
                continue
            
            # Convert bbox to original frame coordinates
            x_coords = [int(p[0] / 3) for p in bbox]
            y_coords = [int(p[1] / 3) + 600 for p in bbox]
            x_center = int(sum(x_coords) / 4)
            y_center = int(sum(y_coords) / 4)
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # Match labels
            for target in self.TARGET_LABELS:
                if target in text_clean or text_clean in target:
                    labels.append({
                        'text': target, 'x': x_center, 'y': y_center,
                        'x_min': x_min, 'x_max': x_max, 'y_min': y_min, 'y_max': y_max,
                        'conf': conf, 'raw': text_clean
                    })
                    break
            
            # Match values
            for target in self.TARGET_VALUES:
                if target in text_clean or text_clean in target:
                    values.append({
                        'text': target, 'x': x_center, 'y': y_center,
                        'conf': conf, 'raw': text_clean
                    })
                    break
        
        # Also try partial matches for labels (common OCR errors)
        self._add_partial_label_matches(enhanced, results, 600, labels)
        self._add_partial_value_matches(enhanced, results, 600, values)
        
        if not labels and not values:
            return self._fallback()
        
        # Combine labels and values to find the control row
        all_anchors = labels + values
        if not all_anchors:
            return self._fallback()
        
        # Find the densest horizontal cluster (the control row)
        all_anchors.sort(key=lambda a: a['y'])
        
        # Find horizontal cluster with most anchors
        best_cluster = []
        best_y = None
        
        for anchor in all_anchors:
            cluster = [anchor]
            for other in all_anchors:
                if anchor != other and abs(other['y'] - anchor['y']) <= 20:
                    cluster.append(other)
            if len(cluster) > len(best_cluster):
                best_cluster = cluster
                best_y = int(sum(a['y'] for a in cluster) / len(cluster))
        
        if len(best_cluster) < 2:
            return self._fallback()
        
        # Compute bounds from cluster
        cluster = best_cluster
        xs = [a['x'] for a in cluster]
        ys = [a['y'] for a in cluster]
        
        # Check if all items in cluster have x_min/x_max
        has_bounds = all('x_min' in a and 'x_max' in a for a in cluster)
        if has_bounds:
            x_min = min(a['x_min'] for a in cluster)
            x_max = max(a['x_max'] for a in cluster)
        else:
            # Fallback: estimate from x centers
            xs = [a['x'] for a in cluster]
            x_min = min(xs) - 100
            x_max = max(xs) + 100
        
        row_y = best_y
        
        # Use actual cluster bounds with padding instead of fixed width
        # The cluster already has the correct x_min/x_max from the anchors
        if has_bounds:
            x_min = max(0, x_min - 50)  # 50px padding left
            x_max = min(1920, x_max + 50)  # 50px padding right
        else:
            # Fallback: estimate from x centers with generous padding
            xs = [a['x'] for a in cluster]
            x_min = max(0, min(xs) - 150)
            x_max = min(1920, max(xs) + 150)
        
        row_y = best_y
        
        # Use cluster bounds with generous padding, but also ensure minimum width
        # based on typical control row structure (spans most of screen width)
        if has_bounds:
            x_min = max(0, x_min - 100)
            x_max = min(1920, x_max + 100)
        else:
            xs = [a['x'] for a in cluster]
            x_min = max(0, min(xs) - 200)
            x_max = min(1920, max(xs) + 200)
        
        # The control row typically extends to the right edge of the viewport
        # Use the right edge of the frame as the right boundary
        x_max = 1910  # Near right edge
        
        # Ensure minimum row width based on UI structure (~1300px for full row)
        detected_width = x_max - x_min
        min_expected_width = 1300
        if detected_width < min_expected_width:
            cluster_center_x = int(sum(a['x'] for a in cluster) / len(cluster))
            half_width = min_expected_width // 2
            x_min = max(0, cluster_center_x - half_width)
            x_max = min(1920, cluster_center_x + half_width)
        
        row_y = best_y
        
        y_top = max(0, row_y - 40)
        y_bottom = row_y + 80
        
        x_left = x_min
        x_right = x_max
        
        # Build position dicts
        label_positions = {l['text']: (l['x'], l['y']) for l in labels}
        value_positions = {v['text']: (v['x'], v['y']) for v in values}
        
        # Detect layout
        layout = self._detect_layout(frame, row_y + 80)
        
        return ControlRowLocation(
            y_top=row_y - 40,
            y_bottom=row_y + 80,
            x_left=x_left,
            x_right=x_right,
            layout=layout,
            confidence=0.8 if len(best_cluster) >= 4 else 0.5,
            detection_method="ocr_anchor_cluster",
            label_positions={l['text']: (l['x'], l['y']) for l in labels},
            value_positions={v['text']: (v['x'], v['y']) for v in values}
        )
    
    def _add_partial_label_matches(self, enhanced, results, y_offset, labels):
        """Add partial matches for commonly misread labels"""
        partial_patterns = {
            "STRATEGY": ["STRATEG", "STRATGY", "STRATE", "STRAT"],
            "PACE": ["PAC"],
            "TYRE": ["TYR", "TRE"],
            "FUEL": ["FUL", "FUE"],
            "DEFEND": ["DEFEN", "DEFND", "FEND"],
            "PIT": ["PI"],
            "NITRO": ["NITR", "ITRO", "NTR"],
        }
        
        for bbox, text, conf in results:
            if conf < 0.2:
                continue
            text_clean = text.strip().upper()
            if len(text_clean) < 2:
                continue
            
            for target, patterns in self._partial_label_patterns().items():
                for pat in patterns:
                    if pat in text_clean and len(text_clean) >= len(pat):
                        x_coords = [int(p[0] / 3) for p in bbox]
                        y_coords = [int(p[1] / 3) + 600 for p in bbox]
                        x_center = int(sum(x_coords) / 4)
                        y_center = int(sum(y_coords) / 4)
                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)
                        
                        # Avoid duplicates
                        if not any(l['text'] == target for l in labels):
                            labels.append({
                                'text': target, 'x': x_center,
                                'y': y_center,
                                'x_min': x_min, 'x_max': x_max,
                                'y_min': y_min, 'y_max': y_max,
                                'conf': conf, 'raw': text_clean
                            })
    
    def _partial_label_patterns(self):
        return {
            "STRATEGY": ["STRATEG", "STRATGY", "STRATE", "STRAT"],
            "PACE": ["PAC"],
            "TYRE": ["TYR", "TRE"],
            "FUEL": ["FUL", "FUE"],
            "DEFEND": ["DEFEN", "DEFND", "FEND"],
            "PIT": ["PI"],
            "NITRO": ["NITR", "ITRO", "NTR"],
        }
    
    def _add_partial_value_matches(self, enhanced, results, y_offset, values):
        """Add partial matches for commonly misread values"""
        partial_patterns = {
            "BALANCED": ["ANCED", "BALANC", "BAL"],
            "ATTACK": ["ATTAC", "TACK", "ATCK"],
            "SAFE": ["SAF"],
            "NEUTRAL": ["NEUT", "NEUITRAL", "NEUTRL", "NEUT"],
            "CONSERVE": ["CONSERV", "CONSV", "SERVE"],
            "PUSH": ["PUS", "USH"],
            "SOFT": ["SOF", "OFT"],
            "MEDIUM": ["MEDIU", "DIUM", "MED"],
            "HARD": ["HAR", "ARD"],
            "RICH": ["RIC", "ICH"],
            "STANDARD": ["STANDA", "TANDAR", "STD"],
            "LEAN": ["LEA", "EAN"],
            "BOX BOX": ["BOX", "BOXBOX"],
        }
        
        for bbox, text, conf in results:
            if conf < 0.2:
                continue
            text_clean = text.strip().upper()
            if len(text_clean) < 2:
                continue
            
            for target, patterns in self._partial_value_patterns().items():
                for pat in patterns:
                    if pat in text_clean and len(text_clean) >= len(pat):
                        if not any(v['text'] == target for v in values):
                            x_coords = [int(p[0] / 3) for p in bbox]
                            y_coords = [int(p[1] / 3) + 600 for p in bbox]
                            x_center = int(sum(x_coords) / 4)
                            y_center = int(sum(y_coords) / 4)
                            x_min, x_max = min(x_coords), max(x_coords)
                            y_min, y_max = min(y_coords), max(y_coords)
                            values.append({
                                'text': target, 'x': x_center,
                                'y': y_center,
                                'x_min': x_min, 'x_max': x_max,
                                'y_min': y_min, 'y_max': y_max,
                                'conf': conf, 'raw': text_clean
                            })
    
    def _partial_value_patterns(self):
        return {
            "BALANCED": ["ANCED", "BALANC", "BAL"],
            "ATTACK": ["ATTAC", "TACK", "ATCK"],
            "SAFE": ["SAF"],
            "NEUTRAL": ["NEUT", "NEUITRAL", "NEUTRL", "NEUT"],
            "CONSERVE": ["CONSERV", "CONSV", "SERVE"],
            "PUSH": ["PUS", "USH"],
            "SOFT": ["SOF", "OFT"],
            "MEDIUM": ["MEDIU", "DIUM", "MED"],
            "HARD": ["HAR", "ARD"],
            "RICH": ["RIC", "ICH"],
            "STANDARD": ["STANDA", "TANDAR", "STD"],
            "LEAN": ["LEA", "EAN"],
            "BOX BOX": ["BOX", "BOXBOX"],
        }
    
    def _detect_layout(self, frame: np.ndarray, control_row_bottom: int) -> LayoutType:
        h, w = frame.shape[:2]
        if control_row_bottom >= frame.shape[0] - 50:
            return LayoutType.UNKNOWN
        
        check_region = frame[control_row_bottom:min(frame.shape[0], control_row_bottom + 150), 0:frame.shape[1]]
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
            y_top=800, y_bottom=950, x_left=200, x_right=1720,
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
    
    print("=== Testing Improved UI Localizer on Ground Truth ===")
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
    for val, pos in location.value_positions.items():
        print("    {}: x={}, y={}".format(val, pos[0], pos[1]))
    
    expected_y_top, expected_y_bottom = 830, 910
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
    cv2.imwrite('frames/ground_truth/localizer_v3_debug.png', debug)
    print("Saved debug to frames/ground_truth/localizer_v3_debug.png")


if __name__ == "__main__":
    test_localizer()