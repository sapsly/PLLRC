import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Test frame at t=150s (frame 5496) where "LIVE RACE" was detected
video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

frame_idx = 5496  # t=150s - LIVE RACE detected
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
ret, frame = cap.read()
cap.release()

if not ret:
    print("Failed to read frame")
    exit()

h, w = frame.shape[:2]
print(f"Frame {frame_idx} (t={frame_idx/fps:.1f}s): {w}x{h}")

cv2.imwrite("frames/target_test_live_full.png", frame)

# Candidate regions for active race UI
candidates = {
    'top_left':      frame[20:120, 20:350],
    'top_center':    frame[20:120, w//2-250:w//2+250],
    'top_right':     frame[20:120, w-370:w-20],
    
    'left_upper':    frame[80:220, 20:280],
    'left_mid':      frame[220:360, 20:280],
    'left_lower':    frame[360:500, 20:280],
    
    'right_upper':   frame[80:220, w-300:w-20],
    'right_mid':     frame[220:360, w-300:w-20],
    'right_lower':   frame[360:500, w-300:w-20],
    
    'bottom_left':   frame[h-140:h-20, 20:350],
    'bottom_center': frame[h-140:h-20, w//2-250:w//2+250],
    'bottom_right':  frame[h-140:h-20, w-370:w-20],
    
    # Center regions (for optional UI)
    'mid_left':      frame[h//2-80:h//2+80, 20:350],
    'mid_center':    frame[h//2-80:h//2+80, w//2-250:w//2+250],
    'mid_right':     frame[h//2-80:h//2+80, w-370:w-20],
}

os.makedirs("frames/target_candidates_live", exist_ok=True)
for name, region in candidates.items():
    if region.size > 0:
        cv2.imwrite(f"frames/target_candidates_live/{name}.png", region)

print(f"Saved {len(candidates)} candidate regions")

# OCR each
print("\n=== OCR Results ===")
for name, region in candidates.items():
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