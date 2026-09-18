import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

frames_dir = "frames/race6_key"
frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])

for frame_name in frames:
    frame_path = os.path.join(frames_dir, frame_name)
    frame = cv2.imread(frame_path)
    h, w = frame.shape[:2]
    
    print(f"\n=== {frame_name} ===")
    
    # Check multiple regions
    regions = {
        'top_left': frame[30:180, 30:500],
        'top_center': frame[30:180, w//2-250:w//2+250],
        'top_right': frame[30:180, w-530:w-30],
        'left_mid': frame[h//2-150:h//2+150, 0:300],
        'right_mid': frame[h//2-150:h//2+150, w-300:w],
        'bottom_left': frame[h-180:h-30, 30:500],
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