"""
Targeted visual search for Strategy/Pace/Defend controls
Searches for repeated UI structures: 3-button groups and 2-state toggles
"""
import cv2
import numpy as np
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum


@dataclass
class ButtonCandidate:
    x: int
    y: int
    w: int
    h: int
    area: float
    aspect: float
    color_profile: Dict[str, float]  # color -> percentage
    mean_bgr: Tuple[float, float, float]
    mean_hsv: Tuple[float, float, float]


@dataclass
class ControlGroup:
    name: str
    buttons: List[ButtonCandidate]
    center_x: float
    center_y: float
    width: float
    height: float
    button_spacing: float
    layout_consistency: float  # 0-1
    evidence: Dict


# HSV color ranges
COLOR_RANGES = {
    'green': [(35, 50, 50), (85, 255, 255)],
    'red': [(0, 50, 50), (10, 255, 255)],
    'red2': [(170, 50, 50), (180, 255, 255)],
    'yellow': [(15, 50, 50), (35, 255, 255)],
    'blue': [(90, 50, 50), (130, 255, 255)],
    'white': [(0, 0, 200), (180, 30, 255)],
    'dark': [(0, 0, 0), (180, 255, 60)],  # low value
}


def detect_buttons(region: np.ndarray, min_area: int = 80, max_area: int = 8000) -> List[ButtonCandidate]:
    """Detect button-like contours with color profiling"""
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    
    # Multi-threshold edge detection
    edges1 = cv2.Canny(gray, 30, 100)
    edges2 = cv2.Canny(gray, 50, 150)
    edges = cv2.bitwise_or(edges1, edges2)
    
    # Morphological closing to connect button edges
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    buttons = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = w / h if h > 0 else 0
            
            # Filter: reasonable button aspect ratio
            if 0.3 < aspect < 4.0:
                # Color profile
                roi_hsv = hsv[y:y+h, x:x+w]
                roi_bgr = region[y:y+h, x:x+w]
                
                if roi_hsv.size == 0:
                    continue
                
                color_profile = {}
                total = roi_hsv.shape[0] * roi_hsv.shape[1]
                
                for color_name, ranges in COLOR_RANGES.items():
                    if color_name == 'red':
                        mask1 = cv2.inRange(roi_hsv, ranges[0], ranges[1])
                        mask2 = cv2.inRange(roi_hsv, COLOR_RANGES['red2'][0], COLOR_RANGES['red2'][1])
                        mask = mask1 | mask2
                    else:
                        mask = cv2.inRange(roi_hsv, ranges[0], ranges[1])
                    pct = np.sum(mask > 0) / total * 100
                    if pct > 0.5:
                        color_profile[color_name] = pct
                
                mean_bgr = tuple(np.mean(roi_bgr, axis=(0, 1)))
                mean_hsv = tuple(np.mean(roi_hsv, axis=(0, 1)))
                
                buttons.append(ButtonCandidate(
                    x=x, y=y, w=w, h=h, area=area, aspect=aspect,
                    color_profile=color_profile,
                    mean_bgr=mean_bgr, mean_hsv=mean_hsv
                ))
    
    return buttons


def find_horizontal_groups(buttons: List[ButtonCandidate], max_y_diff: int = 15, max_x_gap: int = 50) -> List[List[ButtonCandidate]]:
    """Find horizontally aligned button groups (3-button or 2-button)"""
    if len(buttons) < 2:
        return []
    
    # Sort by y then x
    buttons_sorted = sorted(buttons, key=lambda b: (b.y, b.x))
    
    groups = []
    used = set()
    
    for i, btn1 in enumerate(buttons_sorted):
        if i in used:
            continue
        
        group = [btn1]
        used.add(i)
        
        # Find neighbors to the right on same horizontal line
        for j, btn2 in enumerate(buttons_sorted):
            if j in used:
                continue
            
            y_diff = abs(btn2.y - btn1.y)
            x_gap = btn2.x - (btn1.x + btn1.w)
            
            if y_diff <= max_y_diff and 0 < x_gap < max_x_gap:
                group.append(btn2)
                used.add(j)
        
        if len(group) >= 2:
            # Sort group by x
            group.sort(key=lambda b: b.x)
            groups.append(group)
    
    return groups


def analyze_group_consistency(group: List[ButtonCandidate]) -> Dict:
    """Analyze how consistent a button group is (size, spacing, alignment)"""
    if len(group) < 2:
        return {'consistency': 0.0}
    
    widths = [b.w for b in group]
    heights = [b.h for b in group]
    areas = [b.area for b in group]
    
    # Coefficient of variation (lower = more consistent)
    w_cv = np.std(widths) / np.mean(widths) if np.mean(widths) > 0 else 1.0
    h_cv = np.std(heights) / np.mean(heights) if np.mean(heights) > 0 else 1.0
    a_cv = np.std(areas) / np.mean(areas) if np.mean(areas) > 0 else 1.0
    
    # Spacing consistency
    spacings = []
    for i in range(len(group) - 1):
        gap = group[i+1].x - (group[i].x + group[i].w)
        spacings.append(gap)
    
    s_cv = np.std(spacings) / np.mean(spacings) if len(spacings) > 1 and np.mean(spacings) > 0 else 0.0
    
    # Y-alignment consistency
    ys = [b.y for b in group]
    y_cv = np.std(ys) / np.mean(ys) if np.mean(ys) > 0 else 0.0
    
    # Overall consistency (0-1, higher = more consistent)
    consistency = 1.0 - min(1.0, (w_cv + h_cv + a_cv + s_cv + y_cv) / 5.0)
    
    return {
        'consistency': consistency,
        'width_cv': w_cv,
        'height_cv': h_cv,
        'area_cv': a_cv,
        'spacing_cv': s_cv,
        'y_cv': y_cv,
        'mean_spacing': np.mean(spacings) if spacings else 0,
        'button_count': len(group),
        'widths': widths,
        'heights': heights,
        'spacings': spacings
    }


def search_frame(frame_path: str, frame_name: str) -> Dict[str, List[ControlGroup]]:
    """Search a frame for control group candidates"""
    frame = cv2.imread(frame_path)
    if frame is None:
        return {}
    
    h, w = frame.shape[:2]
    
    # Search regions - focus on areas NOT in optional UI bottom
    # Divide frame into horizontal bands
    search_bands = [
        (0, 180, 'top_band'),
        (180, 360, 'upper_mid'),
        (360, 540, 'mid'),
        (540, 720, 'lower_mid'),
        (720, 900, 'upper_bottom'),
        (900, 1080, 'bottom_band'),
    ]
    
    # Also search vertical strips
    search_strips = [
        (0, 300, 'left_strip'),
        (300, 1620, 'center_strip'),
        (1620, 1920, 'right_strip'),
    ]
    
    all_groups = []
    
    # Search horizontal bands
    for y_start, y_end, band_name in search_bands:
        band = frame[y_start:y_end, 0:w]
        if band.size == 0:
            continue
        
        buttons = detect_buttons(band)
        if len(buttons) < 2:
            continue
        
        # Adjust button coordinates to full frame
        for btn in buttons:
            btn.y += y_start
        
        groups = find_horizontal_groups(buttons)
        for group in groups:
            consistency_data = analyze_group_consistency(group)
            
            if consistency_data['consistency'] > 0.4:  # Minimum threshold
                center_x = np.mean([b.x + b.w/2 for b in group])
                center_y = np.mean([b.y + b.h/2 for b in group])
                group_w = (group[-1].x + group[-1].w) - group[0].x
                group_h = max(b.h for b in group)
                
                all_groups.append(ControlGroup(
                    name=f"{band_name}_group_{len(all_groups)}",
                    buttons=group,
                    center_x=center_x,
                    center_y=center_y,
                    width=group_w,
                    height=group_h,
                    button_spacing=consistency_data['mean_spacing'],
                    layout_consistency=consistency_data['consistency'],
                    evidence={
                        'band': band_name,
                        'consistency_data': consistency_data,
                        'button_colors': [{k: v for k, v in b.color_profile.items()} for b in group],
                        'button_positions': [(b.x, b.y, b.w, b.h) for b in group]
                    }
                ))
    
    # Sort by consistency
    all_groups.sort(key=lambda g: g.layout_consistency, reverse=True)
    
    # Filter: keep top candidates per band, and only 2-3 button groups
    filtered = []
    seen_bands = set()
    for g in all_groups:
        band = g.evidence['band']
        btn_count = len(g.buttons)
        if btn_count in [2, 3] and g.layout_consistency > 0.5:
            if band not in seen_bands or len([f for f in filtered if f.evidence['band'] == band]) < 2:
                filtered.append(g)
                seen_bands.add(band)
    
    return {'all': all_groups, 'filtered': filtered}


def compare_layouts(results_with_optional: Dict, results_without_optional: Dict) -> Dict:
    """Compare control group positions between layouts"""
    comparison = {}
    
    for layout_name, results in [('with_optional', results_with_optional), ('without_optional', results_without_optional)]:
        for g in results['filtered']:
            key = f"{g.evidence['band']}_btns{len(g.buttons)}"
            if key not in comparison:
                comparison[key] = {'with_optional': None, 'without_optional': None}
            comparison[key][layout_name] = {
                'center': (g.center_x, g.center_y),
                'size': (g.width, g.height),
                'spacing': g.button_spacing,
                'consistency': g.layout_consistency,
                'button_count': len(g.buttons)
            }
    
    return comparison


def main():
    frames = {
        'race6_with_optional_t90s': 'frames/search/race6_with_optional_t90s.png',
        'race6_with_optional_t150s': 'frames/search/race6_with_optional_t150s.png',
        'race1_no_optional_t60s': 'frames/search/race1_no_optional_t60s.png',
        'race1_no_optional_t100s': 'frames/search/race1_no_optional_t100s.png',
        'race5_no_optional_t40s': 'frames/search/race5_no_optional_t40s.png',
    }
    
    all_results = {}
    
    print("=== SEARCHING FRAMES ===\n")
    for name, path in frames.items():
        if not os.path.exists(path):
            print(f"Missing: {path}")
            continue
        
        results = search_frame(path, name)
        all_results[name] = results
        
        print(f"--- {name} ---")
        for g in results['filtered']:
            btn_count = len(g.buttons)
            colors = g.evidence['button_colors']
            pos = g.evidence['button_positions']
            print(f"  {g.name}: {btn_count} buttons, consistency={g.layout_consistency:.2f}")
            print(f"    Center: ({g.center_x:.0f}, {g.center_y:.0f})")
            print(f"    Size: {g.width:.0f}x{g.height:.0f}, Spacing: {g.button_spacing:.0f}")
            print(f"    Buttons: {pos}")
            for i, c in enumerate(colors):
                print(f"      Btn {i}: {c}")
            print()
    
    # Compare Race 6 (with) vs Race 1 (without) at similar race phase
    print("=== LAYOUT COMPARISON ===")
    comp = compare_layouts(
        all_results.get('race6_with_optional_t90s', {'filtered': []}),
        all_results.get('race1_no_optional_t60s', {'filtered': []})
    )
    
    for key, data in comp.items():
        w = data['with_optional']
        wo = data['without_optional']
        if w and wo:
            dx = w['center'][0] - wo['center'][0]
            dy = w['center'][1] - wo['center'][1]
            print(f"\n{key}:")
            print(f"  With optional:    center=({w['center'][0]:.0f},{w['center'][1]:.0f}) size={w['size'][0]:.0f}x{w['size'][1]:.0f} spacing={w['spacing']:.0f} cons={w['consistency']:.2f}")
            print(f"  Without optional: center=({wo['center'][0]:.0f},{wo['center'][1]:.0f}) size={wo['size'][0]:.0f}x{wo['size'][1]:.0f} spacing={wo['spacing']:.0f} cons={wo['consistency']:.2f}")
            print(f"  Shift: dx={dx:+.0f}, dy={dy:+.0f}")
        elif w:
            print(f"\n{key}: ONLY in with_optional")
        elif wo:
            print(f"\n{key}: ONLY in without_optional")
    
    # Also compare across time in same race
    print("\n=== TEMPORAL STABILITY (Race 6) ===")
    comp2 = compare_layouts(
        all_results.get('race6_with_optional_t90s', {'filtered': []}),
        all_results.get('race6_with_optional_t150s', {'filtered': []})
    )
    
    for key, data in comp2.items():
        t90 = data['with_optional']  # t90s
        t150 = data['without_optional']  # t150s
        if t90 and t150:
            dx = t150['center'][0] - t90['center'][0]
            dy = t150['center'][1] - t90['center'][1]
            print(f"{key}: dx={dx:+.0f}, dy={dy:+.0f} (should be ~0)")
    
    return all_results


if __name__ == "__main__":
    results = main()