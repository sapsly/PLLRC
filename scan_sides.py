import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

# Check key times for left/right UI
times = [10, 30, 60, 90, 120, 150, 180, 210]

for t in times:
    frame_idx = int(t * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret:
        continue
    
    h, w = frame.shape[:2]
    
    # Check left and right vertical strips
    regions = {
        'left_upper': frame[100:400, 20:300],
        'left_mid': frame[h//2-150:h//2+150, 20:300],
        'left_lower': frame[h-400:h-100, 20:300],
        'right_upper': frame[100:400, w-320:w-20],
        'right_mid': frame[h//2-150:h//2+150, w-320:w-20],
        'right_lower': frame[h-400:h-100, w-320:w-20],
    }
    
    print(f"\nt={t}s:")
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for prep_name, img in [('e', enhanced), ('t', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            texts = []
            for _, text, conf in results:
                if conf > 0.35 and len(text.strip()) > 1:
                    texts.append(text.strip())
            if texts:
                print(f"  {name}_{prep_name}: {', '.join(texts[:5])}")
                break

cap.release()