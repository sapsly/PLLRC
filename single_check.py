import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

frame_idx = int(60 * fps)
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
ret, frame = cap.read()
cap.release()

if ret:
    h, w = frame.shape[:2]
    mc = frame[h//2-100:h//2+100, w//2-250:w//2+250]
    gray = cv2.cvtColor(mc, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    for prep_name, img in [('e', enhanced), ('t', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        for _, text, conf in results:
            if conf > 0.35 and len(text.strip()) > 2:
                print('{}: "{}" ({:.2f})'.format(prep_name, text.strip(), conf))