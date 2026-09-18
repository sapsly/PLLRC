import cv2
import os
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

# Quick test on just a few frames from race 1 (middle and end)
race_dir = "frames/race1"
frames = sorted([f for f in os.listdir(race_dir) if f.endswith('.png') and not f.startswith('debug') and not f.startswith('ocr')])

# Test middle and last frames
test_frames = [frames[len(frames)//2], frames[-2], frames[-1]]

for frame in test_frames:
    frame_path = os.path.join(race_dir, frame)
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    print(f"\n--- {frame} ({w}x{h}) ---")
    
    # Focus on specific regions where UI might be
    regions = {
        'top_left': img[30:160, 30:350],
        'top_center': img[30:160, w//2-175:w//2+175],
        'top_right': img[30:160, w-380:w-30],
        'mid_left': img[h//2-80:h//2+80, 30:350],
        'bottom_left': img[h-160:h-30, 30:350],
        'bottom_center': img[h-160:h-30, w//2-175:w//2+175],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Just try original and threshold
        for suffix, proc in [('orig', gray), ('thresh', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])]:
            results = reader.readtext(proc, detail=1, paragraph=False)
            for bbox, text, conf in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    print(f"  {name}_{suffix}: '{text.strip()}' (conf: {conf:.2f})")
                    break