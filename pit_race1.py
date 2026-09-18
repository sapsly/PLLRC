import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

video_path = r'Training\PLLRC_Videos\Race_001_06-09-2026.mp4'
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

for t in [30, 60, 90, 120]:
    frame_idx = int(t * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret:
        continue
    
    right = frame[832:952, 1600:1910]
    gray = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    max_val = np.max(gray)
    
    if max_val > 50:
        up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(up)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        reader = easyocr.Reader(['en'], gpu=False)
        
        for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
            results = reader.readtext(img, detail=1, paragraph=False)
            found = False
            for bbox, text, conf in results:
                if conf > 0.2 and len(text.strip()) > 1:
                    if not found:
                        print('Race 1 t={}s {} ==='.format(t, prep_name))
                        found = True
                    print('  "{}" (conf:{:.2f})'.format(text.strip(), conf))

cap.release()