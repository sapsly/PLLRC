"""
Visual Detector Prototype for Strategy/Pace/Defend Controls
Tests hypothesis that controls are icon/color-based indicators
"""
import cv2
import numpy as np
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum


class StrategyState(Enum):
    SAFE = "safe"
    NEUTRAL = "neutral"
    ATTACK = "attack"
    UNKNOWN = "unknown"


class PaceState(Enum):
    CONSERVE = "conserve"
    NEUTRAL = "neutral"
    PUSH = "push"
    UNKNOWN = "unknown"


class DefendState(Enum):
    ON = "on"
    OFF = "off"
    UNKNOWN = "unknown"


@dataclass
class ControlDetection:
    control_name: str
    detected: bool
    region: Tuple[int, int, int, int]  # x, y, w, h
    button_count: int
    button_positions: List[Tuple[int, int, int, int]]  # relative x, y, w, h
    estimated_state: str
    confidence: float
    evidence: Dict
    method: str


class VisualDetector:
    """Prototype detector for Strategy/Pace/Defend visual controls"""
    
    # Hypothesized regions (1920x1080) - from previous investigation
    REGIONS = {
        'strategy': (50, 950, 250, 110),      # x, y, w, h
        'pace': (710, 950, 500, 110),
        'defend': (1620, 400, 280, 100),
    }
    
    # HSV color ranges for state detection
    COLOR_RANGES = {
        'green': [(35, 50, 50), (85, 255, 255)],      # Active/selected
        'red': [(0, 50, 50), (10, 255, 255), (170, 50, 50), (180, 255, 255)],  # Inactive/off
        'yellow': [(15, 50, 50), (35, 255, 255)],     # Warning/neutral
        'blue': [(90, 50, 50), (130, 255, 255)],      # Info
        'white': [(0, 0, 200), (180, 30, 255)],       # Bright text/icons
    }
    
    def __init__(self):
        self.debug_dir = "frames/detector_debug"
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def crop_region(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Crop a region from frame"""
        x, y, w, h = region
        h_frame, w_frame = frame.shape[:2]
        x = max(0, min(x, w_frame - 1))
        y = max(0, min(y, h_frame - 1))
        w = min(w, w_frame - x)
        h = min(h, h_frame - y)
        return frame[y:y+h, x:x+w]
    
    def detect_buttons(self, region: np.ndarray, min_area: int = 100, max_area: int = 5000) -> List[Tuple[int, int, int, int]]:
        """Detect button-like contours in region"""
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Try multiple edge detection approaches
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = w / h if h > 0 else 0
                if 0.4 < aspect < 3.0:  # Button-like
                    buttons.append((x, y, w, h))
        
        # Sort left-to-right, top-to-bottom
        buttons.sort(key=lambda b: (b[1], b[0]))
        return buttons
    
    def analyze_button_colors(self, region: np.ndarray, buttons: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """Analyze color content of each button"""
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        results = []
        
        for i, (x, y, w, h) in enumerate(buttons):
            btn_roi = hsv[y:y+h, x:x+w]
            if btn_roi.size == 0:
                results.append({'index': i, 'dominant_color': 'none', 'color_scores': {}})
                continue
            
            # Calculate color scores
            scores = {}
            total_pixels = btn_roi.shape[0] * btn_roi.shape[1]
            
            # Green
            green_mask = cv2.inRange(btn_roi, self.COLOR_RANGES['green'][0], self.COLOR_RANGES['green'][1])
            scores['green'] = np.sum(green_mask > 0) / total_pixels * 100
            
            # Red (two ranges)
            red_mask1 = cv2.inRange(btn_roi, self.COLOR_RANGES['red'][0], self.COLOR_RANGES['red'][1])
            red_mask2 = cv2.inRange(btn_roi, self.COLOR_RANGES['red'][2], self.COLOR_RANGES['red'][3])
            red_mask = red_mask1 | red_mask2
            scores['red'] = np.sum(red_mask > 0) / total_pixels * 100
            
            # Yellow
            yellow_mask = cv2.inRange(btn_roi, self.COLOR_RANGES['yellow'][0], self.COLOR_RANGES['yellow'][1])
            scores['yellow'] = np.sum(yellow_mask > 0) / total_pixels * 100
            
            # Blue
            blue_mask = cv2.inRange(btn_roi, self.COLOR_RANGES['blue'][0], self.COLOR_RANGES['blue'][1])
            scores['blue'] = np.sum(blue_mask > 0) / total_pixels * 100
            
            # White
            white_mask = cv2.inRange(btn_roi, self.COLOR_RANGES['white'][0], self.COLOR_RANGES['white'][1])
            scores['white'] = np.sum(white_mask > 0) / total_pixels * 100
            
            # Dominant color (with threshold)
            dominant = 'none'
            max_score = 0
            for color, score in scores.items():
                if score > max_score and score > 2.0:  # Minimum 2% threshold
                    max_score = score
                    dominant = color
            
            results.append({
                'index': i,
                'dominant_color': dominant,
                'color_scores': scores,
                'bbox': (x, y, w, h)
            })
        
        return results
    
    def classify_strategy(self, button_analysis: List[Dict]) -> Tuple[StrategyState, float]:
        """Classify strategy state from 3 buttons (Safe, Neutral, Attack)"""
        if len(button_analysis) != 3:
            return StrategyState.UNKNOWN, 0.0
        
        # Expected order: Safe (left), Neutral (middle), Attack (right)
        # Selected button typically shows green/bright, others red/dim
        
        green_scores = [b['color_scores'].get('green', 0) for b in button_analysis]
        red_scores = [b['color_scores'].get('red', 0) for b in button_analysis]
        yellow_scores = [b['color_scores'].get('yellow', 0) for b in button_analysis]
        
        # Find button with highest green (selected)
        max_green_idx = np.argmax(green_scores)
        max_green_val = green_scores[max_green_idx]
        
        # Find button with highest red (unselected)
        max_red_idx = np.argmax(red_scores)
        max_red_val = red_scores[max_red_idx]
        
        # Confidence based on separation
        confidence = 0.0
        if max_green_val > 5.0 and max_green_val > max_red_val:
            confidence = min(0.9, max_green_val / 30.0)
            if max_green_idx == 0:
                return StrategyState.SAFE, confidence
            elif max_green_idx == 1:
                return StrategyState.NEUTRAL, confidence
            elif max_green_idx == 2:
                return StrategyState.ATTACK, confidence
        
        # Fallback: check yellow (sometimes neutral is yellow)
        max_yellow_idx = np.argmax(yellow_scores)
        max_yellow_val = yellow_scores[max_yellow_idx]
        if max_yellow_val > 5.0 and max_yellow_idx == 1:
            return StrategyState.NEUTRAL, min(0.7, max_yellow_val / 30.0)
        
        return StrategyState.UNKNOWN, 0.0
    
    def classify_pace(self, button_analysis: List[Dict]) -> Tuple[PaceState, float]:
        """Classify pace state from 3 buttons (Conserve, Neutral, Push)"""
        if len(button_analysis) != 3:
            return PaceState.UNKNOWN, 0.0
        
        # Expected order: Conserve (left), Neutral (middle), Push (right)
        green_scores = [b['color_scores'].get('green', 0) for b in button_analysis]
        red_scores = [b['color_scores'].get('red', 0) for b in button_analysis]
        yellow_scores = [b['color_scores'].get('yellow', 0) for b in button_analysis]
        
        max_green_idx = np.argmax(green_scores)
        max_green_val = green_scores[max_green_idx]
        
        confidence = 0.0
        if max_green_val > 5.0:
            confidence = min(0.9, max_green_val / 30.0)
            if max_green_idx == 0:
                return PaceState.CONSERVE, confidence
            elif max_green_idx == 1:
                return PaceState.NEUTRAL, confidence
            elif max_green_idx == 2:
                return PaceState.PUSH, confidence
        
        # Fallback: yellow for neutral
        max_yellow_idx = np.argmax(yellow_scores)
        max_yellow_val = yellow_scores[max_yellow_idx]
        if max_yellow_val > 5.0 and max_yellow_idx == 1:
            return PaceState.NEUTRAL, min(0.7, max_yellow_val / 30.0)
        
        return PaceState.UNKNOWN, 0.0
    
    def classify_defend(self, button_analysis: List[Dict]) -> Tuple[DefendState, float]:
        """Classify defend state from 2 buttons (On, Off) or toggle"""
        if len(button_analysis) < 1:
            return DefendState.UNKNOWN, 0.0
        
        # For 2 buttons: On (left), Off (right)
        # For toggle: single button changes color
        
        if len(button_analysis) == 2:
            green_scores = [b['color_scores'].get('green', 0) for b in button_analysis]
            red_scores = [b['color_scores'].get('red', 0) for b in button_analysis]
            
            max_green_idx = np.argmax(green_scores)
            max_green_val = green_scores[max_green_idx]
            
            if max_green_val > 5.0:
                confidence = min(0.9, max_green_val / 30.0)
                if max_green_idx == 0:
                    return DefendState.ON, confidence
                elif max_green_idx == 1:
                    return DefendState.OFF, confidence
        
        elif len(button_analysis) == 1:
            # Single toggle - check if green (on) or red (off)
            green = button_analysis[0]['color_scores'].get('green', 0)
            red = button_analysis[0]['color_scores'].get('red', 0)
            
            if green > red and green > 5.0:
                return DefendState.ON, min(0.8, green / 30.0)
            elif red > green and red > 5.0:
                return DefendState.OFF, min(0.8, red / 30.0)
        
        return DefendState.UNKNOWN, 0.0
    
    def detect_control(self, frame: np.ndarray, control_name: str) -> ControlDetection:
        """Detect a single control in frame"""
        region_coords = self.REGIONS.get(control_name)
        if not region_coords:
            return ControlDetection(
                control_name=control_name,
                detected=False,
                region=(0,0,0,0),
                button_count=0,
                button_positions=[],
                estimated_state="unknown",
                confidence=0.0,
                evidence={},
                method="no_region_defined"
            )
        
        x, y, w, h = region_coords
        region = self.crop_region(frame, region_coords)
        
        if region.size == 0:
            return ControlDetection(
                control_name=control_name,
                detected=False,
                region=region_coords,
                button_count=0,
                button_positions=[],
                estimated_state="unknown",
                confidence=0.0,
                evidence={'error': 'empty_region'},
                method="empty_region"
            )
        
        # Detect buttons
        buttons = self.detect_buttons(region)
        
        # Analyze colors
        button_analysis = self.analyze_button_colors(region, buttons)
        
        # Classify based on control type
        if control_name == 'strategy':
            state, confidence = self.classify_strategy(button_analysis)
        elif control_name == 'pace':
            state, confidence = self.classify_pace(button_analysis)
        elif control_name == 'defend':
            state, confidence = self.classify_defend(button_analysis)
        else:
            state, confidence = StrategyState.UNKNOWN, 0.0
        
        detected = len(buttons) > 0 and confidence > 0.0
        
        return ControlDetection(
            control_name=control_name,
            detected=detected,
            region=region_coords,
            button_count=len(buttons),
            button_positions=[b['bbox'] for b in button_analysis],
            estimated_state=state.value,
            confidence=confidence,
            evidence={
                'button_analysis': button_analysis,
                'region_shape': region.shape,
                'region_mean_bgr': np.mean(region, axis=(0,1)).tolist(),
                'region_mean_hsv': np.mean(cv2.cvtColor(region, cv2.COLOR_BGR2HSV), axis=(0,1)).tolist()
            },
            method="hsv_contour_classification"
        )
    
    def detect_all(self, frame: np.ndarray) -> Dict[str, ControlDetection]:
        """Detect all three controls"""
        results = {}
        for name in ['strategy', 'pace', 'defend']:
            results[name] = self.detect_control(frame, name)
        return results
    
    def save_debug_crops(self, frame: np.ndarray, frame_id: str):
        """Save cropped regions for visual inspection"""
        for name, region_coords in self.REGIONS.items():
            x, y, w, h = region_coords
            region = self.crop_region(frame, region_coords)
            if region.size > 0:
                cv2.imwrite(f"{self.debug_dir}/{frame_id}_{name}_crop.png", region)
                
                # Also save with detected buttons drawn
                buttons = self.detect_buttons(region)
                debug_img = region.copy()
                for i, (bx, by, bw, bh) in enumerate(buttons):
                    cv2.rectangle(debug_img, (bx, by), (bx+bw, by+bh), (0, 255, 0), 2)
                    cv2.putText(debug_img, str(i), (bx, by-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.imwrite(f"{self.debug_dir}/{frame_id}_{name}_buttons.png", debug_img)
                
                # HSV visualization
                hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
                cv2.imwrite(f"{self.debug_dir}/{frame_id}_{name}_hsv.png", hsv)
                
                # Color masks
                for color_name, ranges in self.COLOR_RANGES.items():
                    if color_name == 'red':
                        mask1 = cv2.inRange(hsv, ranges[0], ranges[1])
                        mask2 = cv2.inRange(hsv, ranges[2], ranges[3])
                        mask = mask1 | mask2
                    else:
                        mask = cv2.inRange(hsv, ranges[0], ranges[1])
                    cv2.imwrite(f"{self.debug_dir}/{frame_id}_{name}_mask_{color_name}.png", mask)


def test_detector():
    """Run detector on test frames"""
    detector = VisualDetector()
    
    # Test frames
    test_frames = []
    for race in ['race6', 'race1']:
        race_dir = f"frames/detector_test/{race}"
        if os.path.exists(race_dir):
            for f in sorted(os.listdir(race_dir)):
                if f.endswith('.png'):
                    test_frames.append((race, os.path.join(race_dir, f)))
    
    print(f"Testing on {len(test_frames)} frames\n")
    
    all_results = {}
    
    for race, frame_path in test_frames:
        frame_id = os.path.basename(frame_path).replace('.png', '')
        frame = cv2.imread(frame_path)
        
        if frame is None:
            print(f"Failed to load {frame_path}")
            continue
        
        # Save debug crops
        detector.save_debug_crops(frame, f"{race}_{frame_id}")
        
        # Detect all controls
        results = detector.detect_all(frame)
        all_results[f"{race}_{frame_id}"] = results
        
        print(f"=== {race} {frame_id} ===")
        for name, det in results.items():
            status = "DETECTED" if det.detected else "NOT DETECTED"
            print(f"  {name.upper()}: {status}")
            print(f"    Region: {det.region}")
            print(f"    Buttons: {det.button_count}")
            print(f"    State: {det.estimated_state} (conf: {det.confidence:.2f})")
            print(f"    Button positions: {det.button_positions}")
            
            # Show color evidence
            for btn in det.evidence.get('button_analysis', []):
                colors = btn['color_scores']
                dom = btn['dominant_color']
                print(f"    Btn {btn['index']}: dom={dom}, G={colors.get('green',0):.1f}% R={colors.get('red',0):.1f}% Y={colors.get('yellow',0):.1f}% B={colors.get('blue',0):.1f}% W={colors.get('white',0):.1f}%")
        print()
    
    return all_results


if __name__ == "__main__":
    results = test_detector()