import cv2
import os
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

video_path = r"Training\PLLRC_Videos\Race_001_06-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

# Save frames around change points for inspection
change_frames = [828, 858, 888, 918, 1290, 1320, 1350, 1380, 1410, 1440]
os.makedirs("frames/change_inspection", exist_ok=True)

for frame_idx in change_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"frames/change_inspection/race1_frame_{frame_idx}.png", frame)
        # Also save specific regions
        h, w = frame.shape[:2]
        regions = {
            'full': frame,
            'top_20pct': frame[0:int(h*0.2), :],
            'top_left': frame[30:180, 30:400],
            'top_center': frame[30:180, w//2-200:w//2+200],
            'top_right': frame[30:180, w-430:w-30],
            'left_25pct': frame[:, 0:int(w*0.25)],
            'right_25pct': frame[:, int(w*0.75):],
            'mid_left': frame[h//2-100:h//2+100, 30:400],
            'bottom_20pct': frame[int(h*0.8):, :],
        }
        for name, region in regions.items():
            if region.size > 0:
                cv2.imwrite(f"frames/change_inspection/race1_frame_{frame_idx}_{name}.png", region)

cap.release()
print("Saved frames for inspection")

# Now do comprehensive OCR on these frames with multiple preprocessing methods
for frame_idx in change_frames:
    frame_path = f"frames/change_inspection/race1_frame_{frame_idx}.png"
    if not os.path.exists(frame_path):
        continue
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    print(f"\n=== Frame {frame_idx} ===")
    
    # Check many regions
    regions = {
        'tl': img[20:200, 20:500],
        'tc': img[20:200, w//2-250:w//2+250],
        'tr': img[20:200, w-520:w-20],
        'ml': img[h//2-100:h//2+100, 20:500],
        'bl': img[h-200:h-20, 20:500],
        'bc': img[h-200:h-20, w//2-250:w//2+250],
        'br': img[h-200:h-20, w-520:w-20],
        'left_mid': img[h//3:2*h//3, 20:300],
        'right_mid': img[h//3:2*h//3, w-320:w-20],
    }
    
    for name, region in regions.items():
        if region.size == 0:
            continue
        
        # Try multiple preprocessing approaches
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        methods = [
            ('orig', gray),
            ('thresh', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ('thresh_inv', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
            ('adaptive', cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
        ]
        
        for method_name, proc in methods:
            results = reader.readtext(proc, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    print(f"  {name}_{method_name}: '{text.strip()}' (conf:{conf:.2f})")
                    break