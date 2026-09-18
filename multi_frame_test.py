import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Test multiple candidate frames from race 6
video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

# Frames with high visual change scores
test_frames = [
    (5475, "t=149.4s"),
    (5548, "t=151.4s"), 
    (7695, "t=210s"),
    (8103, "t=221.1s"),
    (366, "t=10s"),
    (732, "t=20s"),
]

for frame_idx, label in test_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret:
        continue
    
    h, w = frame.shape[:2]
    print(f"\n=== Frame {frame_idx} ({label}) ===")
    
    # Quick check top, left, right regions
    regions = {
        'tl': frame[20:120, 20:350],
        'tc': frame[20:120, w//2-250:w//2+250],
        'tr': frame[20:120, w-370:w-20],
        'lu': frame[80:220, 20:280],
        'ru': frame[80:220, w-300:w-20],
        'mc': frame[h//2-80:h//2+80, w//2-250:w//2+250],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for prep_name, img in [('e', enhanced), ('t', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    text_clean = text.strip()
                    lower = text_clean.lower()
                    is_target = any(kw in lower for kw in ['safe', 'neutral', 'attack', 'conserve', 'push', 'defend', ' on ', ' off ', 'strategy', 'pace'])
                    marker = " ***TARGET***" if is_target else ""
                    print(f"  {name}_{prep_name}: '{text_clean}' (conf:{conf:.2f}){marker}")
                    break

cap.release()