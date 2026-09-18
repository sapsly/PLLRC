import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Focus on specific frames and regions with upscaling
for frame_idx in [366, 2198, 5496, 7695]:
    frame_path = f'frames/race6_samples/frame_{frame_idx}.png'
    if not os.path.exists(frame_path):
        continue
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    print(f"\n=== Frame {frame_idx} ===")
    
    # Key regions - upscale 4x for better OCR
    regions = {
        'tl': img[20:200, 20:500],
        'tc': img[20:200, w//2-250:w//2+250],
        'tr': img[20:200, w-520:w-20],
        'ml': img[h//2-100:h//2+100, 20:500],
        'left_ui': img[150:400, 20:350],  # Possible strategy/pace area
        'right_ui': img[150:400, w-370:w-20],  # Possible defend area
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        
        # Upscale 4x
        up = cv2.resize(region, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        
        # Try CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Try threshold
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Just try enhanced
        results = reader.readtext(enhanced, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.2 and len(text.strip()) > 1:
                print(f'  {name}_enhanced: "{text.strip()}" (conf:{conf:.2f})')
                break
        
        # Try threshold
        results = reader.readtext(thresh, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.2 and len(text.strip()) > 1:
                print(f'  {name}_thresh: "{text.strip()}" (conf:{conf:.2f})')
                break