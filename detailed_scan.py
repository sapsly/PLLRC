import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

# Check t=60s where we saw driver attributes - check smaller regions
frame_idx = int(60 * fps)
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
ret, frame = cap.read()
cap.release()

if ret:
    h, w = frame.shape[:2]
    
    # Check many small regions
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
    
    print("t=60s - detailed scan:")
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for prep_name, img in [('e', enhanced), ('t', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            for _, text, conf in results:
                if conf > 0.3 and len(text.strip()) > 1:
                    print(f"  {name}_{prep_name}: '{text.strip()}' (conf:{conf:.2f})")
                    break