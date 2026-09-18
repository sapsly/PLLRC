import cv2
import numpy as np
import os

# Analyze the visual characteristics of the UI regions in race 6 frames
for frame_idx in [366, 2198, 5496, 7695]:
    frame_path = f'frames/race6_samples/frame_{frame_idx}.png'
    if not os.path.exists(frame_path):
        continue
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    print(f"\n=== Frame {frame_idx} ===")
    
    # Analyze color distributions in key regions
    regions = {
        'tl': img[20:200, 20:500],
        'tc': img[20:200, w//2-250:w//2+250],
        'tr': img[20:200, w-520:w-20],
        'ml': img[h//2-100:h//2+100, 20:500],
        'full_top': img[0:200, :],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        
        # Color analysis
        mean_bgr = np.mean(region, axis=(0,1))
        mean_hsv = np.mean(cv2.cvtColor(region, cv2.COLOR_BGR2HSV), axis=(0,1))
        
        # Check for specific colors (UI elements often have distinct colors)
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # Green-ish (could be "On" or positive status)
        green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
        green_pct = np.sum(green_mask > 0) / green_mask.size * 100
        
        # Red-ish (could be "Off" or negative status)
        red_mask1 = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
        red_mask2 = cv2.inRange(hsv, (170, 50, 50), (180, 255, 255))
        red_mask = red_mask1 | red_mask2
        red_pct = np.sum(red_mask > 0) / red_mask.size * 100
        
        # Blue-ish
        blue_mask = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))
        blue_pct = np.sum(blue_mask > 0) / blue_mask.size * 100
        
        # Yellow/Orange
        yellow_mask = cv2.inRange(hsv, (15, 50, 50), (35, 255, 255))
        yellow_pct = np.sum(yellow_mask > 0) / yellow_mask.size * 100
        
        # White/bright
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        white_pct = np.sum(gray > 200) / gray.size * 100
        
        print(f"  {name}: BGR={mean_bgr}, HSV={mean_hsv}")
        print(f"    Green: {green_pct:.1f}%, Red: {red_pct:.1f}%, Blue: {blue_pct:.1f}%, Yellow: {yellow_pct:.1f}%, White: {white_pct:.1f}%")