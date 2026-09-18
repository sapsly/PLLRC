import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

for race_num in [15, 16]:
    print(f"\n=== Race {race_num} ===")
    for frame_idx in [0, 1837, 3674, 5511, 7249] if race_num == 15 else [0, 1797, 3594, 5391, 7088]:
        frame_path = f'frames/check_race{race_num}_{frame_idx}.png'
        if not os.path.exists(frame_path):
            continue
        img = cv2.imread(frame_path)
        h, w = img.shape[:2]
        
        # Check multiple regions
        regions = {
            'top': img[30:180, 30:600],
            'top_left': img[30:180, 30:400],
            'top_center': img[30:180, w//2-200:w//2+200],
            'top_right': img[30:180, w-430:w-30],
            'mid_left': img[h//2-80:h//2+80, 30:400],
            'bottom': img[h-180:h-30, 30:600],
        }
        
        for name, region in regions.items():
            if region.size == 0:
                continue
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            results = reader.readtext(thresh, detail=1, paragraph=False)
            for _, t, c in results:
                if c > 0.4 and len(t.strip()) > 1:
                    print(f"  Frame {frame_idx} [{name}]: '{t}' (conf:{c:.2f})")
                    break