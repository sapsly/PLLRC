import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Check left and right side regions more carefully
test_frames = [
    "frames/race6_samples/frame_366.png",
    "frames/race6_samples/frame_5496.png",
    "frames/race6_samples/frame_7695.png",
]

for frame_path in test_frames:
    if not os.path.exists(frame_path):
        continue
    frame = cv2.imread(frame_path)
    h, w = frame.shape[:2]
    
    print(f"\n=== {os.path.basename(frame_path)} ===")
    
    # Check left and right vertical strips
    regions = {
        'left_full': frame[:, 0:int(w*0.2)],
        'right_full': frame[:, int(w*0.8):],
        'left_upper': frame[100:500, 0:int(w*0.2)],
        'right_upper': frame[100:500, int(w*0.8):],
        'left_mid': frame[h//2-200:h//2+200, 0:int(w*0.2)],
        'right_mid': frame[h//2-200:h//2+200, int(w*0.8):],
        'left_lower': frame[h-500:h-100, 0:int(w*0.2)],
        'right_lower': frame[h-500:h-100, int(w*0.8):],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Upscale 2x
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for prep_name, img in [('enh', enhanced), ('thr', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.25 and len(text.strip()) > 1:
                    print(f"  {name}_{prep_name}: '{text.strip()}' (conf:{conf:.2f})")
                    break