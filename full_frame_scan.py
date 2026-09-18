import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Check a few frames with full region scan
test_frames = [
    "frames/race6_timeline/frame_366_t10s.png",
    "frames/race6_timeline/frame_2198_t60s.png",
    "frames/race6_timeline/frame_5496_t150s.png",
    "frames/race6_timeline/frame_7695_t210s.png",
]

for frame_path in test_frames:
    frame = cv2.imread(frame_path)
    h, w = frame.shape[:2]
    
    print(f"\n=== {os.path.basename(frame_path)} ===")
    
    # Define a grid of regions to scan
    regions = {}
    # Top row
    regions['tl'] = frame[20:150, 20:400]
    regions['tc'] = frame[20:150, w//2-200:w//2+200]
    regions['tr'] = frame[20:150, w-420:w-20]
    # Middle row
    regions['ml'] = frame[h//2-80:h//2+80, 20:400]
    regions['mc'] = frame[h//2-80:h//2+80, w//2-200:w//2+200]
    regions['mr'] = frame[h//2-80:h//2+80, w-420:w-20]
    # Bottom row
    regions['bl'] = frame[h-150:h-20, 20:400]
    regions['bc'] = frame[h-150:h-20, w//2-200:w//2+200]
    regions['br'] = frame[h-150:h-20, w-420:w-20]
    # Left vertical
    regions['lv'] = frame[100:h-100, 20:250]
    # Right vertical
    regions['rv'] = frame[100:h-100, w-270:w-20]
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for prep_name, img in [('e', enhanced), ('t', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.35 and len(text.strip()) > 1:
                    print('  {}_{}: "{}" ({:.2f})'.format(name, prep_name, text.strip(), conf))
                    break