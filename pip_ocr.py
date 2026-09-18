"""
PIP - Perception/ML Component for PLLRC
OCR/Perception System for Pit Lane Legends Ranked Racing
"""
import cv2
import numpy as np
import easyocr
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from enum import Enum
import json


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
    STANDARD = "standard"           # No optional section
    WITH_OPTIONAL = "with_optional"  # Optional section present
    UNKNOWN = "unknown"


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: List[List[int]]
    region_name: str
    preprocessing: str


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
    
    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "pace": self.pace.value,
            "defend": self.defend.value,
            "optional_ui_present": self.optional_ui_present,
            "layout": self.layout.value,
            "raw_ocr": [{"text": r.text, "confidence": r.confidence, "region": r.region_name, "preprocessing": r.preprocessing} for r in self.raw_ocr_results],
            "confidence": self.confidence,
            "frame_timestamp": self.frame_timestamp,
            "frame_index": self.frame_index
        }


class ImagePreprocessor:
    """Image preprocessing for OCR optimization"""
    
    @staticmethod
    def enhance_for_ocr(gray: np.ndarray) -> Dict[str, np.ndarray]:
        """Apply multiple preprocessing strategies"""
        results = {}
        
        # Original
        results['original'] = gray
        
        # CLAHE contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        results['clahe'] = clahe.apply(gray)
        
        # Otsu threshold
        _, results['otsu'] = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Inverted Otsu
        _, results['otsu_inv'] = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Adaptive threshold
        results['adaptive'] = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations for text cleanup
        kernel = np.ones((2, 2), np.uint8)
        results['morph'] = cv2.morphologyEx(results['otsu'], cv2.MORPH_CLOSE, kernel)
        
        return results


class LayoutDetector:
    """Detects which UI layout is visible in the frame"""
    
    # Region definitions (relative to frame size)
    REGIONS = {
        'top_left': (0.015, 0.015, 0.26, 0.185),      # x, y, w, h as fractions
        'top_center': (0.35, 0.015, 0.30, 0.185),
        'top_right': (0.73, 0.015, 0.26, 0.185),
        'mid_left': (0.015, 0.40, 0.26, 0.20),
        'mid_center': (0.35, 0.40, 0.30, 0.20),
        'bottom_left': (0.015, 0.80, 0.26, 0.185),
        'bottom_center': (0.35, 0.80, 0.30, 0.185),
        'bottom_right': (0.73, 0.80, 0.26, 0.185),
    }
    
    def __init__(self):
        self.layout_templates = {}
    
    def extract_regions(self, frame: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract predefined regions from frame"""
        h, w = frame.shape[:2]
        regions = {}
        
        for name, (rx, ry, rw, rh) in self.REGIONS.items():
            x = int(rx * w)
            y = int(ry * h)
            rw_px = int(rw * w)
            rh_px = int(rh * h)
            
            if x + rw_px <= w and y + rh_px <= h:
                regions[name] = frame[y:y+rh_px, x:x+rw_px]
        
        return regions
    
    def detect_layout(self, frame: np.ndarray) -> UILayout:
        """Detect which UI layout is present"""
        h, w = frame.shape[:2]
        
        # Check for optional section indicators in middle region
        mid_region = frame[int(h*0.35):int(h*0.65), int(w*0.3):int(w*0.7)]
        gray = cv2.cvtColor(mid_region, cv2.COLOR_BGR2GRAY)
        
        # Look for UI panel characteristics (rectangular regions with borders)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        panel_count = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500:  # Significant rectangular region
                x, y, w_c, h_c = cv2.boundingRect(cnt)
                aspect = w_c / h_c if h_c > 0 else 0
                if 0.5 < aspect < 5.0:  # Panel-like aspect ratio
                    panel_count += 1
        
        # Also check top region for standard UI elements
        top_region = frame[0:int(h*0.2), :]
        top_gray = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
        _, top_thresh = cv2.threshold(top_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        top_text_pixels = np.sum(top_thresh > 200)
        
        # Heuristic: if middle has panel-like structures, optional UI is present
        if panel_count >= 2 and top_text_pixels > 1000:
            return UILayout.WITH_OPTIONAL
        elif top_text_pixels > 1000:
            return UILayout.STANDARD
        else:
            return UILayout.UNKNOWN


class TextRecognizer:
    """Handles OCR text recognition with confidence scoring"""
    
    def __init__(self, languages=['en'], gpu=False):
        self.reader = easyocr.Reader(languages, gpu=gpu)
        self.preprocessor = ImagePreprocessor()
    
    def recognize_region(self, region: np.ndarray, region_name: str) -> List[OCRResult]:
        """Run OCR on a region with multiple preprocessing strategies"""
        if region.size == 0:
            return []
        
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if len(region.shape) == 3 else region
        
        # Upscale small regions for better OCR
        h, w = gray.shape
        if h < 100 or w < 100:
            scale = max(100/h, 100/w, 2.0)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        processed = self.preprocessor.enhance_for_ocr(gray)
        results = []
        
        for prep_name, proc_img in processed.items():
            try:
                ocr_results = self.reader.readtext(proc_img, detail=1, paragraph=False)
                for bbox, text, conf in ocr_results:
                    if conf > 0.25 and len(text.strip()) > 1:
                        results.append(OCRResult(
                            text=text.strip(),
                            confidence=conf,
                            bbox=bbox,
                            region_name=region_name,
                            preprocessing=prep_name
                        ))
            except Exception as e:
                # Silently continue on OCR errors
                pass
        
        # Deduplicate by text content (keep highest confidence)
        unique = {}
        for r in results:
            key = r.text.lower()
            if key not in unique or r.confidence > unique[key].confidence:
                unique[key] = r
        
        return list(unique.values())


class UIParser:
    """Parses OCR results into structured UI observations"""
    
    STRATEGY_KEYWORDS = {
        Strategy.SAFE: ['safe', 'saf', 'safe'],
        Strategy.NEUTRAL: ['neutral', 'neut', 'ntrl', 'ntral'],
        Strategy.ATTACK: ['attack', 'atk', 'att', 'atck'],
    }
    
    PACE_KEYWORDS = {
        Pace.CONSERVE: ['conserve', 'consrv', 'consv', 'save'],
        Pace.NEUTRAL: ['neutral', 'neut', 'ntrl'],
        Pace.PUSH: ['push', 'psh', 'pus'],
    }
    
    DEFEND_KEYWORDS = {
        Defend.ON: ['on', 'active', 'yes', 'enabled'],
        Defend.OFF: ['off', 'inactive', 'no', 'disabled'],
    }
    
    def __init__(self):
        pass
    
    def parse_strategy(self, text: str) -> Strategy:
        text_lower = text.lower()
        for strategy, keywords in self.STRATEGY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return strategy
        return Strategy.UNKNOWN
    
    def parse_pace(self, text: str) -> Pace:
        text_lower = text.lower()
        for pace, keywords in self.PACE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return pace
        return Pace.UNKNOWN
    
    def parse_defend(self, text: str) -> Defend:
        text_lower = text.lower()
        for defend, keywords in self.DEFEND_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return defend
        return Defend.UNKNOWN
    
    def parse_observation(self, ocr_results: List[OCRResult], layout: UILayout) -> UIObservation:
        """Convert OCR results to structured observation"""
        obs = UIObservation(layout=layout)
        
        # Combine all text for searching
        all_text = " ".join([r.text for r in ocr_results])
        
        # Parse each field
        obs.strategy = self.parse_strategy(all_text)
        obs.pace = self.parse_pace(all_text)
        obs.defend = self.parse_defend(all_text)
        obs.optional_ui_present = (layout == UILayout.WITH_OPTIONAL)
        obs.raw_ocr_results = ocr_results
        
        # Calculate overall confidence
        if ocr_results:
            obs.confidence = np.mean([r.confidence for r in ocr_results])
        else:
            obs.confidence = 0.0
        
        return obs


class PIPOCRSystem:
    """Main OCR system for Pit Lane Legends"""
    
    def __init__(self, languages=['en'], gpu=False):
        self.layout_detector = LayoutDetector()
        self.text_recognizer = TextRecognizer(languages, gpu)
        self.ui_parser = UIParser()
    
    def process_frame(self, frame: np.ndarray, frame_index: int = 0, timestamp: float = 0.0) -> UIObservation:
        """Process a single frame and return structured observation"""
        
        # 1. Detect layout
        layout = self.layout_detector.detect_layout(frame)
        
        # 2. Extract regions based on layout
        regions = self.layout_detector.extract_regions(frame)
        
        # 3. Run OCR on all regions
        all_ocr_results = []
        for region_name, region_img in regions.items():
            results = self.text_recognizer.recognize_region(region_img, region_name)
            all_ocr_results.extend(results)
        
        # 4. Parse into structured observation
        observation = self.ui_parser.parse_observation(all_ocr_results, layout)
        observation.frame_index = frame_index
        observation.frame_timestamp = timestamp
        
        return observation
    
    def process_video(self, video_path: str, sample_rate: float = 1.0) -> List[UIObservation]:
        """Process video at specified sample rate (seconds between frames)"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        interval = int(fps * sample_rate)
        observations = []
        
        for frame_idx in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            
            timestamp = frame_idx / fps
            obs = self.process_frame(frame, frame_idx, timestamp)
            observations.append(obs)
        
        cap.release()
        return observations


def main():
    """Test the OCR system on available videos"""
    system = PIPOCRSystem(gpu=False)
    
    video_files = [
        r"Training\PLLRC_Videos\Race_001_06-09-2026.mp4",
        r"Training\PLLRC_Videos\Race_005_07-09-2026.mp4",
        r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4",
        r"Training\PLLRC_Videos\Race_007_07-09-2026.mp4",
    ]
    
    for video_path in video_files:
        print(f"\n{'='*60}")
        print(f"Processing: {video_path}")
        print(f"{'='*60}")
        
        observations = system.process_video(video_path, sample_rate=5.0)  # Every 5 seconds
        
        for obs in observations:
            print(f"\nFrame {obs.frame_index} (t={obs.frame_timestamp:.1f}s):")
            print(f"  Layout: {obs.layout.value}")
            print(f"  Strategy: {obs.strategy.value}")
            print(f"  Pace: {obs.pace.value}")
            print(f"  Defend: {obs.defend.value}")
            print(f"  Optional UI: {obs.optional_ui_present}")
            print(f"  Confidence: {obs.confidence:.2f}")
            if obs.raw_ocr_results:
                print(f"  OCR Results:")
                for r in obs.raw_ocr_results:
                    print(f"    [{r.region_name}/{r.preprocessing}] '{r.text}' (conf:{r.confidence:.2f})")


if __name__ == "__main__":
    main()