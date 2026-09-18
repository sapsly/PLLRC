import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Check just a few key frames
for frame_idx in [828, 858, 888, 1290, 1320, 1350]:
    frame_path = f'frames/change_inspection/race1_frame_{frame_idx}.png'
    if not os.path.exists(frame_path):
        continue
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    print(f'\n=== Frame {frame_idx} ===')
    
    # Just check top-left and top-center
    regions = {
        'tl': img[20:180, 20:500],
        'tc': img[20:180, w//2-250:w//2+250],
        'ml': img[h//2-80:h//2+80, 20:500],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        results = reader.readtext(thresh, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.3 and len(text.strip()) > 1:
                print(f'  {name}: "{text.strip()}" (conf:{conf:.2f})')
                break