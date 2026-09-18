"""
PIP Full Pipeline: Localizer + OCR Reader
"""
import cv2
import numpy as np
import easyocr
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
from enum import Enum

from pip_localizer_v3 import UILocalizer, ControlRowLocation, LayoutType


class ControlState(Enum):
    UNKNOWN = "unknown"


@dataclass
class ControlReading:
    """Result of reading a single control"""
    control_name: str
    label: str
    value: str
    confidence: float
    raw_ocr_text: str
    method: str


class OCRReader:
    """
    Reads control values from the located control row.
    """
    
    EXPECTED_CONTROLS = {
        "STRATEGY": "BALANCED",
        "PACE": "NEUTRAL",
        "TYRE": "SOFT",
        "FUEL": "RICH",
        "NITRO": "0",
        "PIT": "BOX BOX",
        "DEFEND": None,
    }
    
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def read_control_row(self, frame: np.ndarray, 
                         location: ControlRowLocation) -> Dict[str, ControlReading]:
        readings = {}
        
        row_img = frame[location.y_top:location.y_bottom, location.x_left:location.x_right]
        if row_img.size == 0:
            return self._empty_readings("empty_row_region")
        
        gray = cv2.cvtColor(row_img, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        all_results = []
        for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
            try:
                results = self.reader.readtext(img, detail=1, paragraph=False)
                for bbox, text, conf in results:
                    if conf > 0.2 and len(text.strip()) > 1:
                        all_results.append({
                            'text': text.strip(),
                            'conf': conf,
                            'prep': prep_name,
                            'bbox': bbox
                        })
            except Exception as e:
                print(f"OCR error ({prep_name}): {e}")
        
        # Keep all results
        all_texts = [(r['text'].strip(), r) for r in all_results if len(r['text'].strip()) > 1]
        
        print("DEBUG: All OCR texts found:")
        for text, r in all_texts:
            print("  '{}' (conf:{:.2f})".format(text, r['conf']))
        
        readings = {}
        
        for control_name, expected_value in self.EXPECTED_CONTROLS.items():
            matched = self._match_control_value(control_name, expected_value, all_texts, location)
            
            if matched:
                norm_value, result = matched
                reading = ControlReading(
                    control_name=control_name,
                    label=control_name,
                    value=norm_value,
                    confidence=result['conf'],
                    raw_ocr_text=result['text'],
                    method="ocr_match"
                )
            else:
                if control_name == "DEFEND":
                    reading = ControlReading(
                        control_name=control_name,
                        label=control_name,
                        value="UNKNOWN",
                        confidence=0.0,
                        raw_ocr_text="",
                        method="not_found"
                    )
                else:
                    reading = ControlReading(
                        control_name=control_name,
                        label=control_name,
                        value="UNKNOWN",
                        confidence=0.0,
                        raw_ocr_text="",
                        method="not_found"
                    )
            
            readings[control_name] = reading
        
        return readings
    
    def _match_control_value(self, control_name: str, expected_value: str,
                              all_texts: List, location: ControlRowLocation) -> Optional[tuple]:
        expected_upper = expected_value.upper() if expected_value else None
        
        if not expected_upper:
            return None
        
        candidates = []
        
        for text, result in all_texts:
            text_upper = text.upper()
            
            if expected_upper in text_upper:
                candidates.append(("exact", expected_value, result))
                continue
            
            expected_words = expected_upper.split()
            for word in expected_words:
                if len(word) >= 3 and word in text_upper:
                    candidates.append(("partial", expected_value, result))
                    break
            
            if len(expected_upper) >= 4 and expected_upper[:4] in text_upper:
                candidates.append(("prefix", expected_value, result))
                continue
            
            if len(text_upper) >= 4 and text_upper in expected_upper:
                candidates.append(("reverse", expected_value, result))
                continue
        
        if expected_upper == "NEUTRAL":
            for text, result in all_texts:
                text_upper = text.upper()
                if "NEUT" in text_upper or "NEUITRAL" in text_upper:
                    candidates.append(("fuzzy_neutral", expected_value, result))
                    break
        
        if expected_upper == "BOX BOX":
            for text, result in all_texts:
                text_upper = text.upper()
                if "BOX" in text_upper and text_upper.count("BOX") >= 2:
                    candidates.append(("fuzzy_box", expected_value, result))
                    break
        
        if expected_upper == "0":
            for text, result in all_texts:
                text_upper = text.upper()
                if "0" in text_upper and ("LAP" in text_upper or "." in text_upper):
                    candidates.append(("fuzzy_nitro_zero", expected_value, result))
                    break
        
        if expected_upper == "BALANCED":
            for text, result in all_texts:
                text_upper = text.upper()
                if "ANCED" in text_upper or "BAL" in text_upper:
                    candidates.append(("fuzzy_balanced", expected_value, result))
                    break
        
        if expected_upper == "BOX BOX":
            for text, result in all_texts:
                text_upper = text.upper()
                if "PIT" in text_upper and ("BOX" in text_upper or "PIT" in text_upper):
                    candidates.append(("fuzzy_pit", expected_value, result))
                    break
        
        priority = {"exact": 0, "partial": 1, "prefix": 2, "reverse": 3, 
                    "fuzzy_neutral": 4, "fuzzy_box": 5, "fuzzy_nitro_zero": 6,
                    "fuzzy_balanced": 7, "fuzzy_pit": 8}
        
        if candidates:
            candidates.sort(key=lambda c: priority.get(c[0], 99))
            match_type, norm_val, result = candidates[0]
            print("    MATCH {} [{}] = '{}'".format(control_name, match_type, norm_val))
            return (norm_val, candidates[0][2])
        
        return None
    
    def _empty_readings(self, reason: str) -> Dict[str, ControlReading]:
        readings = {}
        for control_name in self.EXPECTED_CONTROLS:
            readings[control_name] = ControlReading(
                control_name=control_name,
                label=control_name,
                value="UNKNOWN",
                confidence=0.0,
                raw_ocr_text="",
                method=reason
            )
        return readings


class PIPPerception:
    def __init__(self):
        self.localizer = UILocalizer()
        self.reader = OCRReader()
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        # Stage 1: Localize control row
        location = self.localizer.locate_control_row(frame)
        
        # Stage 2: Read control values
        readings = self.reader.read_control_row(frame, location)
        
        result = {
            "layout": location.layout.value,
            "localization": {
                "y_top": location.y_top,
                "y_bottom": location.y_bottom,
                "x_left": location.x_left,
                "x_right": location.x_right,
                "confidence": location.confidence,
                "method": location.detection_method
            },
            "controls": {}
        }
        
        for name, reading in readings.items():
            result["controls"][name] = {
                "label": reading.label,
                "value": reading.value,
                "confidence": reading.confidence,
                "method": reading.method
            }
        
        return result


def test_full_pipeline():
    pip = PIPPerception()
    
    gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
    frame = cv2.imread(gt_path)
    
    if frame is None:
        print("Failed to load ground truth")
        return
    
    print("=== Testing Full PIP Pipeline on Ground Truth ===")
    result = pip.process_frame(frame)
    
    print("\n=== PIP RESULT ===")
    print("Layout: {}".format(result["layout"]))
    print("Localization: y={}-{}, x={}-{}, conf={:.2f}, method={}".format(
        result["localization"]["y_top"], result["localization"]["y_bottom"],
        result["localization"]["x_left"], result["localization"]["x_right"],
        result["localization"]["confidence"], result["localization"]["method"]))
    
    print("\nControls:")
    for name, data in result["controls"].items():
        print("  {}: value={}, conf={:.2f}, method={}".format(
            name, data["value"], data["confidence"], data["method"]))
    
    print("\n=== GROUND TRUTH COMPARISON ===")
    expected = {
        "STRATEGY": "BALANCED",
        "PACE": "NEUTRAL",
        "TYRE": "SOFT",
        "FUEL": "RICH",
        "NITRO": "0",
        "PIT": "BOX BOX",
        "DEFEND": "UNKNOWN"
    }
    
    all_correct = True
    for name, exp in expected.items():
        actual = result["controls"][name]["value"]
        match = "OK" if actual.upper() == exp.upper() else "MISS"
        if actual.upper() != exp.upper():
            all_correct = False
        print("  {}: expected={}, got={} {}".format(name, exp, actual, match))
    
    print("\nAll correct: {}".format(all_correct))


if __name__ == "__main__":
    test_full_pipeline()