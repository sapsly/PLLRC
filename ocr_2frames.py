import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Just test 2 key frames
for frame_idx in [5496, 7695]:
    frame_path = f"frames/race6_key/frame_{frame_idx}.png"
    frame = cv2.imread(frame_path)
    h, w = frame.shape[:2]
    
    print(f"\n=== frame_{frame_idx} ===")
    
    # Just top-center and left-mid
    regions = {
        'tc': frame[30:180, w//2-250:w//2+250],
        'lm': frame[h//2-150:h//2+150, 0:300],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for prep_name, img in [('enh', enhanced), ('thr', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    print(f"  {name}_{prep_name}: '{text.strip()}' (conf:{conf:.2f})")
                    break