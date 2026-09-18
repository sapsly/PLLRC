import cv2
import numpy as np
import os

# Visual analysis of candidate regions from frame 5496 (LIVE RACE)
frame = cv2.imread("frames/target_test_live_full.png")
h, w = frame.shape[:2]

# Check color characteristics of regions where controls might be
regions = {
    'top_left':      frame[20:120, 20:350],
    'top_center':    frame[20:120, w//2-250:w//2+250],
    'top_right':     frame[20:120, w-370:w-20],
    'left_upper':    frame[80:220, 20:280],
    'left_mid':      frame[220:360, 20:280],
    'left_lower':    frame[360:500, 20:280],
    'right_upper':   frame[80:220, w-300:w-20],
    'right_mid':     frame[220:360, w-300:w-20],
    'right_lower':   frame[360:500, w-300:w-20],
    'mid_left':      frame[h//2-80:h//2+80, 20:350],
    'mid_center':    frame[h//2-80:h//2+80, w//2-250:w//2+250],
    'mid_right':     frame[h//2-80:h//2+80, w-370:w-20],
    'bottom_left':   frame[h-140:h-20, 20:350],
    'bottom_center': frame[h-140:h-20, w//2-250:w//2+250],
    'bottom_right':  frame[h-140:h-20, w-370:w-20],
}

print("=== Color Analysis (looking for UI indicator colors) ===")
for name, region in regions.items():
    if region.size == 0:
        continue
    
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    
    # Green (often "active/on/selected")
    green = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
    # Red (often "inactive/off/danger")  
    red = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255)) | cv2.inRange(hsv, (170, 50, 50), (180, 255, 255))
    # Yellow/Orange (often "warning/caution/neutral")
    yellow = cv2.inRange(hsv, (15, 50, 50), (35, 255, 255))
    # Blue (often "info/cold")
    blue = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))
    # White/bright text
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    white = cv2.inRange(gray, 200, 255)
    
    total = region.shape[0] * region.shape[1]
    g_pct = np.sum(green > 0) / total * 100
    r_pct = np.sum(red > 0) / total * 100
    y_pct = np.sum(yellow > 0) / total * 100
    b_pct = np.sum(blue > 0) / total * 100
    w_pct = np.sum(white > 0) / total * 100
    
    # Only report if significant colored pixels found
    if g_pct > 0.5 or r_pct > 0.5 or y_pct > 0.5 or b_pct > 0.5 or w_pct > 5:
        print(f"{name:15s}: G={g_pct:5.1f}% R={r_pct:5.1f}% Y={y_pct:5.1f}% B={b_pct:5.1f}% W={w_pct:5.1f}%")

# Also check for rectangular button-like contours
print("\n=== Contour Analysis (button-like shapes) ===")
for name, region in regions.items():
    if region.size == 0:
        continue
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    buttons = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 200 < area < 5000:  # Button-sized
            x, y, w_c, h_c = cv2.boundingRect(cnt)
            aspect = w_c / h_c if h_c > 0 else 0
            if 0.5 < aspect < 4.0:  # Button-like aspect
                buttons.append((x, y, w_c, h_c, aspect, area))
    
    if buttons:
        print(f"{name:15s}: {len(buttons)} button-like contours")
        for x, y, w_c, h_c, aspect, area in buttons[:3]:
            print(f"    ({x},{y}) {w_c}x{h_c} aspect={aspect:.2f} area={area:.0f}")