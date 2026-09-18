import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

for frame_idx in [0, 1775, 3550, 5325, 7000]:
    frame_path = f'frames/check_race14_{frame_idx}.png'
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    # Check top region
    top = img[30:180, 30:600]
    gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    results = reader.readtext(thresh, detail=1, paragraph=False)
    texts = []
    for _, t, c in results:
        if c > 0.4 and len(t.strip()) > 1:
            texts.append(f"'{t}' (conf:{c:.2f})")
    
    print(f"Frame {frame_idx}: {texts if texts else '(no text found)'}")