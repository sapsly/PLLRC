import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Check frames with more regions and methods
for frame_idx in [828, 858, 888, 1290, 1320, 1350]:
    frame_path = f'frames/change_inspection/race1_frame_{frame_idx}.png'
    if not os.path.exists(frame_path):
        continue
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    print(f'\n=== Frame {frame_idx} ===')
    
    regions = {
        'tl': img[20:200, 20:500],
        'tc': img[20:200, w//2-250:w//2+250],
        'tr': img[20:200, w-520:w-20],
        'ml': img[h//2-100:h//2+100, 20:500],
        'bl': img[h-200:h-20, 20:500],
        'bc': img[h-200:h-20, w//2-250:w//2+250],
        'left_full': img[:, 0:int(w*0.25)],
        'right_full': img[:, int(w*0.75):],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        
        # Try multiple preprocessing
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        methods = [
            ('orig', gray),
            ('thresh', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ('thresh_inv', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
        ]
        
        for method_name, proc in methods:
            results = reader.readtext(proc, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    print(f'  {name}_{method_name}: "{text.strip()}" (conf:{conf:.2f})')
                    break