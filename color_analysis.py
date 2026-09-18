import cv2
import numpy as np
import os

# Visual analysis of small regions at t=60s
video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

frame_idx = int(60 * fps)
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
ret, frame = cap.read()
cap.release()

if ret:
    h, w = frame.shape[:2]
    
    os.makedirs("frames/debug_regions", exist_ok=True)
    
    regions = {
        'tl_small': frame[30:120, 30:200],
        'tl_med': frame[30:150, 30:300],
        'tr_small': frame[30:120, w-200:w-30],
        'tr_med': frame[30:150, w-300:w-30],
        'left_1': frame[150:250, 30:250],
        'left_2': frame[250:350, 30:250],
        'left_3': frame[350:450, 30:250],
        'left_4': frame[450:550, 30:250],
        'right_1': frame[150:250, w-280:w-30],
        'right_2': frame[250:350, w-280:w-30],
        'right_3': frame[350:450, w-280:w-30],
        'right_4': frame[450:550, w-280:w-30],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        
        # Save original
        cv2.imwrite(f"frames/debug_regions/t60_{name}.png", region)
        
        # Color analysis
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # Check for specific colors
        green = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
        red = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255)) | cv2.inRange(hsv, (170, 50, 50), (180, 255, 255))
        blue = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))
        yellow = cv2.inRange(hsv, (15, 50, 50), (35, 255, 255))
        white = cv2.inRange(cv2.cvtColor(region, cv2.COLOR_BGR2GRAY), 200, 255)
        
        total = region.shape[0] * region.shape[1]
        g_pct = np.sum(green > 0) / total * 100
        r_pct = np.sum(red > 0) / total * 100
        b_pct = np.sum(blue > 0) / total * 100
        y_pct = np.sum(yellow > 0) / total * 100
        w_pct = np.sum(white > 0) / total * 100
        
        if g_pct > 1 or r_pct > 1 or b_pct > 1 or y_pct > 1 or w_pct > 5:
            print(f"{name}: G={g_pct:.1f}% R={r_pct:.1f}% B={b_pct:.1f}% Y={y_pct:.1f}% W={w_pct:.1f}%")