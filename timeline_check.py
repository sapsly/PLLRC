import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

frames_dir = "frames/race6_timeline"
frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])

for frame_name in frames:
    frame_path = os.path.join(frames_dir, frame_name)
    frame = cv2.imread(frame_path)
    h, w = frame.shape[:2]
    
    # Check top center for race UI
    tc = frame[30:180, w//2-250:w//2+250]
    gray = cv2.cvtColor(tc, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    found = False
    for prep_name, img in [('enh', enhanced), ('thr', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.3 and len(text.strip()) > 1:
                print('{}: {} ({})'.format(frame_name, prep_name, text.strip()))
                found = True
                break
        if found:
            break
    if not found:
        print('{}: (no text)'.format(frame_name))