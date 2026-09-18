import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

frame = cv2.imread("frames/target_test_live_full.png")
h, w = frame.shape[:2]

# Just check bottom_left and right_mid - most promising
regions = {
    'bl': frame[h-140:h-20, 20:350],
    'rm': frame[220:360, w-300:w-20],
    'tc': frame[20:120, w//2-250:w//2+250],
}

for name, region in regions.items():
    if region.size == 0:
        continue
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print(f"\n{name}:")
    for prep_name, img in [('e', enhanced), ('t', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.2 and len(text.strip()) > 1:
                print(f"  {prep_name}: '{text.strip()}' (conf:{conf:.2f})")
                break