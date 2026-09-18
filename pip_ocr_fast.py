"""
PIP - Fast test version
"""
import cv2
import numpy as np
import easyocr
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum


class Strategy(Enum):
    SAFE = "safe"
    NEUTRAL = "neutral"
    ATTACK = "attack"
    UNKNOWN = "unknown"


class Pace(Enum):
    CONSERVE = "conserve"
    NEUTRAL = "neutral"
    PUSH = "push"
    UNKNOWN = "unknown"


class Defend(Enum):
    ON = "on"
    OFF = "off"
    UNKNOWN = "unknown"


class UILayout(Enum):
    STANDARD = "standard"
    WITH_OPTIONAL = "with_optional"
    UNKNOWN = "unknown"


@dataclass
class OCRResult:
    text: str
    confidence: float
    region_name: str


@dataclass
class UIObservation:
    strategy: Strategy = Strategy.UNKNOWN
    pace: Pace = Pace.UNKNOWN
    defend: Defend = Defend.UNKNOWN
    optional_ui_present: bool = False
    layout: UILayout = UILayout.UNKNOWN
    raw_ocr_results: List[OCRResult] = field(default_factory=list)
    confidence: float = 0.0
    frame_timestamp: float = 0.0
    frame_index: int = 0


class FastOCRSystem:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def preprocess_fast(self, gray):
        """Fast preprocessing - just CLAHE + Otsu"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return enhanced, thresh
    
    def extract_regions(self, frame):
        h, w = frame.shape[:2]
        regions = {
            'top_left': frame[30:180, 30:500],
            'top_center': frame[30:180, w//2-250:w//2+250],
            'top_right': frame[30:180, w-530:w-30],
            'mid_left': frame[h//2-100:h//2+100, 30:500],
            'bottom_left': frame[h-180:h-30, 30:500],
        }
        return {k: v for k, v in regions.items() if v.size > 0}
    
    def detect_layout(self, frame):
        h, w = frame.shape[:2]
        # Check middle region for optional UI
        mid = frame[int(h*0.35):int(h*0.65), int(w*0.3):int(w*0.7)]
        gray = cv2.cvtColor(mid, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        panels = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:
                x, y, w_c, h_c = cv2.boundingRect(cnt)
                aspect = w_c / h_c if h_c > 0 else 0
                if 0.5 < aspect < 5.0:
                    panels += 1
        
        top = frame[0:int(h*0.2), :]
        top_gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
        _, top_thresh = cv2.threshold(top_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        top_text = np.sum(top_thresh > 200)
        
        if panels >= 2 and top_text > 1000:
            return UILayout.WITH_OPTIONAL
        elif top_text > 1000:
            return UILayout.STANDARD
        return UILayout.UNKNOWN
    
    def recognize_region(self, region, name):
        if region.size == 0:
            return []
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if len(region.shape) == 3 else region
        
        # Upscale if small
        h, w = gray.shape
        if h < 80 or w < 80:
            scale = max(80/h, 80/w, 2.0)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        enhanced, thresh = self.preprocess_fast(gray)
        
        results = []
        for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
            try:
                ocr_results = self.reader.readtext(img, detail=1, paragraph=False)
                for _, text, conf in ocr_results:
                    if conf > 0.25 and len(text.strip()) > 1:
                        results.append(OCRResult(text.strip(), conf, f"{name}_{prep_name}"))
            except:
                pass
        
        # Deduplicate
        unique = {}
        for r in results:
            if r.text.lower() not in unique or r.confidence > unique[r.text.lower()].confidence:
                unique[r.text.lower()] = r
        return list(unique.values())
    
    def parse_observation(self, ocr_results, layout):
        obs = UIObservation(layout=layout)
        
        all_text = " ".join([r.text for r in ocr_results]).lower()
        
        # Strategy keywords
        if any(kw in all_text for kw in ['safe', 'saf']):
            obs.strategy = Strategy.SAFE
        elif any(kw in all_text for kw in ['neutral', 'neut', 'ntrl']):
            obs.strategy = Strategy.NEUTRAL
        elif any(kw in all_text for kw in ['attack', 'atk', 'att']):
            obs.strategy = Strategy.ATTACK
        
        # Pace keywords
        if any(kw in all_text for kw in ['conserve', 'consrv', 'save']):
            obs.pace = Pace.CONSERVE
        elif any(kw in all_text for kw in ['neutral', 'neut', 'ntrl']):
            obs.pace = Pace.NEUTRAL
        elif any(kw in all_text for kw in ['push', 'psh']):
            obs.pace = Pace.PUSH
        
        # Defend keywords
        if any(kw in all_text for kw in [' on ', 'on\n', 'active', 'enabled']):
            obs.defend = Defend.ON
        elif any(kw in all_text for kw in [' off ', 'off\n', 'inactive', 'disabled']):
            obs.defend = Defend.OFF
        
        obs.optional_ui_present = (layout == UILayout.WITH_OPTIONAL)
        obs.raw_ocr_results = ocr_results
        obs.confidence = np.mean([r.confidence for r in ocr_results]) if ocr_results else 0.0
        
        return obs
    
    def process_frame(self, frame, frame_idx, timestamp):
        layout = self.detect_layout(frame)
        regions = self.extract_regions(frame)
        
        all_results = []
        for name, region in regions.items():
            results = self.recognize_region(region, name)
            all_results.extend(results)
        
        return self.parse_observation(all_results, layout)


def test_on_frames():
    system = FastOCRSystem()
    
    # Test on saved frames from different races
    test_frames = [
        ("race1", "frames/race1/frame_000000.png"),
        ("race1", "frames/race1/frame_002324.png"),
        ("race1", "frames/change_inspection/race1_frame_858.png"),
        ("race1", "frames/change_inspection/race1_frame_1320.png"),
        ("race6", "frames/race6_samples/frame_366.png"),
        ("race6", "frames/race6_samples/frame_2198.png"),
        ("race6", "frames/race6_samples/frame_5496.png"),
        ("race6", "frames/race6_samples/frame_7695.png"),
    ]
    
    for race_name, frame_path in test_frames:
        if not os.path.exists(frame_path):
            print(f"SKIP: {frame_path} not found")
            continue
        
        frame = cv2.imread(frame_path)
        obs = system.process_frame(frame, 0, 0)
        
        print(f"\n{race_name}/{os.path.basename(frame_path)}:")
        print(f"  Layout: {obs.layout.value}")
        print(f"  Strategy: {obs.strategy.value}")
        print(f"  Pace: {obs.pace.value}")
        print(f"  Defend: {obs.defend.value}")
        print(f"  Optional: {obs.optional_ui_present}")
        print(f"  Confidence: {obs.confidence:.2f}")
        for r in obs.raw_ocr_results:
            print(f"    [{r.region_name}] '{r.text}' (conf:{r.confidence:.2f})")


if __name__ == "__main__":
    import os
    test_on_frames()