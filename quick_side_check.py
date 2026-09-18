import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Quick check - just one frame, fewer regions
frame_path = "frames/race6_samples/frame_5496.png"
frame = cv2.imread(frame_path)
h, w = frame.shape[:2]

print(f"Frame: {w}x{h}")

# Just check left and right mid regions
regions = {
    'left_mid': frame[h//2-150:h//2+150, 0:int(w*0.15)],
    'right_mid': frame[h//2-150:h//2+150, int(w*0.85):],
}

for name, region in regions.items():
    if region.size == 0:
        continue
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    for prep_name, img in [('enh', enhanced), ('thr', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.25 and len(text.strip()) > 1:
                print(f"  {name}_{prep_name}: '{text.strip()}' (conf:{conf:.2f})")
                break