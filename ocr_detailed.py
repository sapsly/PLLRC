import cv2
import os
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

# Let's look at frames from the MIDDLE of races, where the actual race UI should be visible
for race_num in [1, 5, 6, 7]:
    race_dir = f"frames/race{race_num}"
    frames = sorted([f for f in os.listdir(race_dir) if f.endswith('.png') and not f.startswith('debug') and not f.startswith('ocr')])
    
    print(f"\n{'='*60}")
    print(f"RACE {race_num} - MID/LATE FRAMES")
    print(f"{'='*60}")
    
    # Test frames from middle and end
    test_frames = frames[len(frames)//2:len(frames)//2+3] + frames[-3:]
    
    for frame in test_frames:
        frame_path = os.path.join(race_dir, frame)
        img = cv2.imread(frame_path)
        h, w = img.shape[:2]
        
        print(f"\n--- {frame} ---")
        
        # The strategy/pace/defend UI is likely in specific locations
        # Let's try more targeted regions based on typical racing game UI layouts
        
        # Top-left area (common for strategy/pace)
        regions = {
            'tl_small': img[40:140, 40:300],
            'tl_med': img[40:180, 40:400],
            'tl_wide': img[20:200, 20:500],
            # Top area - left third
            'top_left_third': img[20:180, 20:w//3],
            # Top area - center third  
            'top_center_third': img[20:180, w//3:2*w//3],
            # Top area - right third
            'top_right_third': img[20:180, 2*w//3:w-20],
            # Bottom left
            'bl_small': img[h-140:h-40, 40:300],
            'bl_med': img[h-180:h-40, 40:400],
            # Bottom center
            'bc_med': img[h-180:h-40, w//2-200:w//2+200],
            # Right side
            'tr_small': img[40:140, w-300:w-40],
            'right_side': img[100:h-100, w-300:w-20],
            # Middle left
            'ml_med': img[h//2-100:h//2+80, 40:350],
        }
        
        for name, region in regions.items():
            if region.size == 0:
                continue
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Try multiple preprocessing approaches
            results_all = []
            
            # Original
            results = reader.readtext(gray, detail=1, paragraph=False)
            results_all.extend([(f"{name}_orig", r) for r in results])
            
            # Threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            results = reader.readtext(thresh, detail=1, paragraph=False)
            results_all.extend([(f"{name}_thresh", r) for r in results])
            
            # Inverted threshold
            _, thresh_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            results = reader.readtext(thresh_inv, detail=1, paragraph=False)
            results_all.extend([(f"{name}_thresh_inv", r) for r in results])
            
            # Adaptive threshold
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            results = reader.readtext(adaptive, detail=1, paragraph=False)
            results_all.extend([(f"{name}_adaptive", r) for r in results])
            
            # Print any results with decent confidence
            for proc_name, (bbox, text, conf) in results_all:
                if conf > 0.3 and len(text.strip()) > 1:
                    print(f"  {proc_name}: '{text.strip()}' (conf: {conf:.2f})")
                    break  # Just show best result per region