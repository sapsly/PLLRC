import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Focus on the promising regions: bottom (green indicators) and right side (red indicators)
frame = cv2.imread("frames/target_test_live_full.png")
h, w = frame.shape[:2]

# Detailed OCR on bottom regions (green = likely active state)
print("=== BOTTOM REGIONS (Green indicators) ===")
bottom_regions = {
    'bottom_left':  frame[h-140:h-20, 20:350],
    'bottom_center': frame[h-140:h-20, w//2-250:w//2+250],
    'bottom_right': frame[h-140:h-20, w-370:w-20],
}

for name, region in bottom_regions.items():
    if region.size == 0:
        continue
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print(f"\n{name}:")
    for prep_name, img in [('e', enhanced), ('t', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.2 and len(text.strip()) > 1:
                print(f"  {prep_name}: '{text.strip()}' (conf:{conf:.2f})")

# Detailed OCR on right side regions (red = likely off state)
print("\n=== RIGHT SIDE REGIONS (Red indicators) ===")
right_regions = {
    'right_upper': frame[80:220, w-300:w-20],
    'right_mid':   frame[220:360, w-300:w-20],
    'right_lower': frame[360:500, w-300:w-20],
}

for name, region in right_regions.items():
    if region.size == 0:
        continue
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print(f"\n{name}:")
    for prep_name, img in [('e', enhanced), ('t', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.2 and len(text.strip()) > 1:
                print(f"  {prep_name}: '{text.strip()}' (conf:{conf:.2f})")

# Top center buttons
print("\n=== TOP CENTER (Button contours) ===")
tc = frame[20:120, w//2-250:w//2+250]
gray = cv2.cvtColor(tc, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(up)
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

for prep_name, img in [('e', enhanced), ('t', thresh)]:
    results = reader.readtext(img, detail=1, paragraph=False)
    for _, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            print(f"  {prep_name}: '{text.strip()}' (conf:{conf:.2f})")