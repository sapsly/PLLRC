import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

for frame_idx in [5496, 7695]:
    frame_path = f'frames/race6_key/frame_{frame_idx}.png'
    frame = cv2.imread(frame_path)
    h, w = frame.shape[:2]
    
    print(f'\n=== frame_{frame_idx} ===')
    
    tc = frame[30:180, w//2-250:w//2+250]
    gray = cv2.cvtColor(tc, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    results = reader.readtext(enhanced, detail=1, paragraph=False)
    for _, text, conf in results:
        if conf > 0.3 and len(text.strip()) > 1:
            print('  tc_enh: "{}" (conf:{:.2f})'.format(text.strip(), conf))
            break
    
    results = reader.readtext(thresh, detail=1, paragraph=False)
    for _, text, conf in results:
        if conf > 0.3 and len(text.strip()) > 1:
            print('  tc_thr: "{}" (conf:{:.2f})'.format(text.strip(), conf))
            break