import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
frame = cv2.imread(gt_path)

pit = frame[832:952, 1600:1910]
gray = cv2.cvtColor(pit, cv2.COLOR_BGR2GRAY)

# Try different preprocessing approaches
# 1. Invert
inverted = cv2.bitwise_not(gray)
# 2. CLAHE + invert
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
clahe_img = clahe.apply(gray)
clahe_inv = cv2.bitwise_not(clahe_img)
# 3. High contrast stretch
contrast = cv2.convertScaleAbs(gray, alpha=10, beta=0)
# 4. Morphological operations
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)

reader = easyocr.Reader(['en'], gpu=False)

images = [
    ('gray', gray),
    ('inverted', inverted),
    ('clahe', clahe_img),
    ('clahe_inv', clahe_inv),
    ('contrast', contrast),
    ('tophat', tophat),
    ('blackhat', blackhat),
]

for name, img in images:
    up = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    results = reader.readtext(up, detail=1, paragraph=False)
    found = False
    for bbox, text, conf in reader.readtext(up, detail=1, paragraph=False):
        if conf > 0.1 and len(text.strip()) > 1:
            if not found:
                print('=== {} ==='.format(name))
                found = True
            print('  "{}" (conf:{:.2f})'.format(text.strip(), conf))
    if not found:
        print('=== {} === (no text found)'.format(name))