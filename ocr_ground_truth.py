import cv2
import numpy as np
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

# Read the control_area at original resolution first
img = cv2.imread('frames/ground_truth/control_area.png')
h, w = img.shape[:2]
print('control_area: {}x{}'.format(w, h))

# Try OCR on the whole control area
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(up)

results = reader.readtext(enhanced, detail=1, paragraph=False)
print('=== OCR Results on control_area (enhanced) ===')
for bbox, text, conf in results:
    if conf > 0.2 and len(text.strip()) > 1:
        print('  "{}" (conf:{:.2f}) at {}'.format(text.strip(), conf, bbox))

# Also try on bottom_300
img2 = cv2.imread('frames/ground_truth/bottom_300.png')
gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
up2 = cv2.resize(gray2, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced2 = clahe.apply(up2)

results2 = reader.readtext(enhanced2, detail=1, paragraph=False)
print('\n=== OCR Results on bottom_300 (enhanced) ===')
for bbox, text, conf in results2:
    if conf > 0.2 and len(text.strip()) > 1:
        print('  "{}" (conf:{:.2f}) at {}'.format(text.strip(), conf, bbox))

# Also try thresholded
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results3 = reader.readtext(thresh, detail=1, paragraph=False)
print('\n=== OCR Results on control_area (thresh) ===')
for bbox, text, conf in results3:
    if conf > 0.2 and len(text.strip()) > 1:
        print('  "{}" (conf:{:.2f}) at {}'.format(text.strip(), conf, bbox))