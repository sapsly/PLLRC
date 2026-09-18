import cv2
import os
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

# Let's check frames at different time points for each race
for race_num in [1, 5, 6, 7]:
    race_dir = f"frames/race{race_num}"
    frames = sorted([f for f in os.listdir(race_dir) if f.endswith('.png') and not f.startswith('debug') and not f.startswith('ocr')])
    
    print(f"\n{'='*60}")
    print(f"RACE {race_num} - ALL FRAMES")
    print(f"{'='*60}")
    
    # Test multiple frames across the video
    indices = [0, len(frames)//4, len(frames)//2, 3*len(frames)//4, -2, -1]
    test_frames = [frames[i] for i in indices if 0 <= i < len(frames)]
    
    for frame in test_frames:
        frame_path = os.path.join(race_dir, frame)
        img = cv2.imread(frame_path)
        h, w = img.shape[:2]
        
        print(f"\n--- {frame} ---")
        
        # Check multiple regions
        regions = {
            'tl': img[30:150, 30:400],
            'tc': img[30:150, w//2-200:w//2+200],
            'tr': img[30:150, w-430:w-30],
            'ml': img[h//2-80:h//2+80, 30:400],
            'bl': img[h-150:h-30, 30:400],
            'bc': img[h-150:h-30, w//2-200:w//2+200],
            'br': img[h-150:h-30, w-430:w-30],
        }
        
        for name, region in regions.items():
            if region.size == 0:
                continue
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            for suffix, proc in [('orig', gray), ('thresh', thresh)]:
                results = reader.readtext(proc, detail=1, paragraph=False)
                for bbox, text, conf in results:
                    if conf > 0.4 and len(text.strip()) > 1:
                        print(f"  {name}_{suffix}: '{text.strip()}' (conf: {conf:.2f})")
                        break