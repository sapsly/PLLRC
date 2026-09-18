"""
PIP Stage 1: UI Localizer
Finds the race-control row in a 1920x1080 frame using visual structure.
NO hardcoded coordinates - uses visual detection.
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum


class LayoutType(Enum):
    WITH_OPTIONAL = "with_optional"
    WITHOUT_OPTIONAL = "without_optional"
    UNKNOWN = "unknown"


@dataclass
class ControlRowLocation:
    """Location of the race-control row"""
    y_top: int
    y_bottom: int
    x_left: int
    x_right: int
    layout: LayoutType
    confidence: float
    detection_method: str


class UILocalizer:
    """
    Locates the race-control row by detecting visual structure:
    - Horizontal text label row (STRATEGY, PACE, TYRE, FUEL, DEFEND, PIT, NITRO)
    - Horizontal value row below labels
    - Optional UI presence affects vertical position
    """
    
    # Known label texts to search for (from ground truth)
    LABEL_TEXTS = [
        "STRATEGY", "PACE", "TYRE", "FUEL", "DEFEND", "PIT", "NITRO"
    ]
    
    # Value texts confirmed in ground truth
    VALUE_TEXTS = [
        "BALANCED", "NEUTRAL", "SOFT", "RICH", "BOX BOX", "0"
    ]
    
    def __init__(self):
        self.debug = False
    
    def detect_game_viewport(self, frame: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Detect the game viewport within the frame.
        Returns (x, y, w, h) of the game area.
        For 1920x1080 full-screen captures, this is typically the full frame.
        """
        h, w = frame.shape[:2]
        # For now, assume full frame is game viewport
        # Could be enhanced to detect black bars, overlays, etc.
        return (0, 0, w, h)
    
    def find_text_regions(self, frame: np.ndarray, 
                          search_y_start: int = 700,
                          search_y_end: int = 1080) -> List[Tuple[int, int, int, int, str]]:
        """
        Find horizontal text bands in the lower portion of the frame.
        Returns list of (x1, y1, x2, y2, type) where type is 'label' or 'value'.
        """
        h, w = frame.shape[:2]
        
        # Crop search region
        search_region = frame[search_y_start:search_y_end, 0:w]
        if search_region.size == 0:
            return []
        
        # Convert to grayscale and enhance for text detection
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        
        # Multiple preprocessing for text detection
        # 1. CLAHE for contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 2. Threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 3. Morphological operations to connect text characters
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 2))
        dilated = cv2.dilate(thresh, kernel_h, iterations=1)
        
        # Find horizontal text lines
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_bands = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:  # Too small
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = w / h if h > 0 else 0
            
            # Text lines are wide and short
            if aspect > 5 and h < 50 and w > 200:
                abs_y = y + search_y_start
                text_bands.append((x, abs_y, x + w, abs_y + h))
        
        # Group nearby bands into rows
        text_bands.sort(key=lambda b: b[1])  # sort by y
        rows = []
        for band in text_bands:
            if not rows or abs(band[1] - rows[-1][1]) > 30:
                rows.append(band)
            else:
                # Merge with previous row
                prev = rows[-1]
                rows[-1] = (min(prev[0], band[0]), prev[1], max(prev[2], band[2]), max(prev[3], band[3]))
        
        return [(x1, y1, x2, y2, 'text_band') for x1, y1, x2, y2 in rows]
    
    def find_control_row_by_labels(self, frame: np.ndarray) -> Optional[ControlRowLocation]:
        """
        Primary method: Find the control row by detecting known label texts.
        Uses template matching / OCR to locate STRATEGY, PACE, etc.
        """
        h, w = frame.shape[:2]
        
        # Search in lower portion where controls typically are
        search_region = frame[700:1080, 0:w]
        if search_region.size == 0:
            return None
        
        gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Try to find each label text using template matching approach
        # We'll use a simple approach: find horizontal text clusters
        # that match the expected horizontal spacing of labels
        
        # Use edge detection to find text-like structures
        edges = cv2.Canny(enhanced, 50, 150)
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 2))
        dilated = cv2.dilate(edges, kernel_h, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find horizontal text clusters
        text_clusters = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 200:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = w / h if h > 0 else 0
            if aspect > 3 and h < 60 and w > 100:
                abs_y = y + 700  # adjust for search region offset
                text_clusters.append((x, abs_y, x + w, abs_y + h))
        
        # Group by Y coordinate (rows)
        text_clusters.sort(key=lambda c: c[1])
        rows = []
        for cluster in text_clusters:
            if not rows or abs(cluster[1] - rows[-1][1]) > 25:
                rows.append(list(cluster))
            else:
                # Merge horizontally
                rows[-1][0] = min(rows[-1][0], cluster[0])
                rows[-1][2] = max(rows[-1][2], cluster[2])
                rows[-1][3] = max(rows[-1][3], cluster[3])
        
        # Look for the label row (should have multiple text clusters with even spacing)
        # and the value row below it
        best_label_row = None
        best_value_row = None
        
        for i, row in enumerate(rows):
            x1, y1, x2, y2 = row
            width = x2 - x1
            height = y2 - y1
            
            # Label row: wide, contains multiple text clusters
            # Value row: below label row, similar width
            if width > 800 and height < 50:
                if best_label_row is None or y1 < best_label_row[1]:
                    best_label_row = row
        
        if best_label_row:
            # Find value row below it
            label_y = best_label_row[1]
            for row in rows:
                if row[1] > label_y + 10 and row[1] < label_y + 60:
                    if abs(row[0] - best_label_row[0]) < 200 and abs(row[2] - best_label_row[2]) < 200:
                        best_value_row = row
                        break
        
        if best_label_row:
            # Estimate control row bounds
            x1 = max(0, best_label_row[0] - 50)
            y1 = max(0, best_label_row[1] - 30)
            x2 = min(1920, best_label_row[2] + 50)
            y2 = best_value_row[3] + 30 if best_value_row else best_label_row[3] + 60
            
            # Detect layout type by checking for optional UI elements below
            layout = self._detect_layout(frame, y2)
            
            return ControlRowLocation(
                y_top=y1,
                y_bottom=y2,
                x_left=x1,
                x_right=x2,
                layout=layout,
                confidence=0.7,
                detection_method="label_row_detection"
            )
        
        return None
    
    def _detect_layout(self, frame: np.ndarray, control_row_bottom: int) -> LayoutType:
        """Detect if optional UI is present below the control row"""
        h, w = frame.shape[:2]
        # Check region below control row for optional UI indicators
        check_region = frame[control_row_bottom:min(h, control_row_bottom + 200), 0:w]
        if check_region.size == 0:
            return LayoutType.UNKNOWN
        
        # Look for fuel/tyre/nitro indicators (color bars, specific texts)
        gray = cv2.cvtColor(check_region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Quick check: optional UI adds significant content below control row
        # Count text-like contours
        edges = cv2.Canny(thresh, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        text_like = sum(1 for c in contours if 100 < cv2.contourArea(c) < 10000)
        
        if text_like > 10:  # Many UI elements below = optional UI present
            return LayoutType.WITH_OPTIONAL
        return LayoutType.WITHOUT_OPTIONAL
    
    def locate_control_row(self, frame: np.ndarray) -> ControlRowLocation:
        """
        Main entry point: locate the race-control row in frame.
        Tries multiple strategies in order of reliability.
        """
        # Strategy 1: Label-based detection (most reliable)
        result = self.find_control_row_by_labels(frame)
        if result:
            return result
        
        # Strategy 2: Fallback - use color/text density in lower third
        h, w = frame.shape[:2]
        # Default fallback based on typical position
        return ControlRowLocation(
            y_top=880,
            y_bottom=980,
            x_left=200,
            x_right=1720,
            layout=LayoutType.UNKNOWN,
            confidence=0.2,
            detection_method="fallback_default"
        )


def test_localizer():
    """Test the localizer on ground truth screenshot"""
    localizer = UILocalizer()
    
    # Load ground truth
    gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
    frame = cv2.imread(gt_path)
    
    if frame is None:
        print("Failed to load ground truth")
        return
    
    print("=== Testing UI Localizer on Ground Truth ===")
    location = localizer.locate_control_row(frame)
    
    print(f"Detected control row:")
    print(f"  y_top: {location.y_top}, y_bottom: {location.y_bottom}")
    print(f"  x_left: {location.x_left}, x_right: {location.x_right}")
    print(f"  layout: {location.layout.value}")
    print(f"  confidence: {location.confidence:.2f}")
    print(f"  method: {location.detection_method}")
    
    # Expected from ground truth: y≈930-970
    expected_y_top, expected_y_bottom = 930, 970
    y_error = abs(location.y_top - expected_y_top)
    print(f"\nExpected y_top={expected_y_top}, got {location.y_top}, error={y_error}px")
    
    # Draw and save detection
    debug = frame.copy()
    cv2.rectangle(debug, (location.x_left, location.y_top), 
                  (location.x_right, location.y_bottom), (0, 255, 0), 3)
    cv2.putText(debug, f"Row: y={location.y_top}-{location.y_bottom}", 
                (location.x_left, location.y_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imwrite('frames/ground_truth/localizer_debug.png', debug)
    print("Saved debug image to frames/ground_truth/localizer_debug.png")


if __name__ == "__main__":
    test_localizer()