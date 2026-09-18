import cv2
import os
import numpy as np

# Let's examine the frames more carefully by saving specific regions for visual inspection
for race_num in [1, 5, 6, 7]:
    race_dir = f"frames/race{race_num}"
    frames = sorted([f for f in os.listdir(race_dir) if f.endswith('.png') and not f.startswith('debug') and not f.startswith('ocr')])
    
    os.makedirs(f"frames/debug_race{race_num}", exist_ok=True)
    
    for frame in frames[:3]:
        frame_path = os.path.join(race_dir, frame)
        img = cv2.imread(frame_path)
        h, w = img.shape[:2]
        
        print(f"\n{race_num}/{frame}: {w}x{h}")
        
        # Save various regions for visual inspection
        regions = {
            'full': img,
            'top_15pct': img[0:int(h*0.15), :],
            'top_10pct': img[0:int(h*0.10), :],
            'top_5pct': img[0:int(h*0.05), :],
            'left_20pct': img[:, 0:int(w*0.2)],
            'right_20pct': img[:, int(w*0.8):],
            'bottom_15pct': img[int(h*0.85):, :],
            'bottom_10pct': img[int(h*0.90):, :],
            # Specific small regions
            'tl_100x300': img[20:120, 20:320],
            'tc_100x500': img[20:120, w//2-250:w//2+250],
            'tr_100x300': img[20:120, w-320:w-20],
            'bl_100x300': img[h-120:h-20, 20:320],
            'bc_100x500': img[h-120:h-20, w//2-250:w//2+250],
            'br_100x300': img[h-120:h-20, w-320:w-20],
        }
        
        for name, region in regions.items():
            if region.size > 0:
                cv2.imwrite(f"frames/debug_race{race_num}/{frame}_{name}.png", region)

print("Done saving debug regions")