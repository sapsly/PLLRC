import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
frame = cv2.imread(gt_path)

# Check middle region for DEFEND/PIT (y=400-500 per earlier hypothesis)
middle = frame[400:500, 1620:1920]
gray = cv2.cvtColor(middle, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(up)
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

reader = easyocr.Reader(['en'], gpu=False)

for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
    results = reader.readtext(img, detail=1, paragraph=False)
    print('=== middle region {} ==='.format(prep_name))
    for bbox, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            x_coords = [int(p[0] / 4) for p in bbox]
            y_coords = [int(p[1] / 4) + 400 for p in bbox]
            x_center = sum(x_coords) / 4
            y_center = sum(y_coords) / 4
            print('  "{}" (conf:{:.2f}) at x={:.0f}, y={:.0f}'.format(text.strip(), conf, x_center, y_center))

cv2.imwrite('frames/ground_truth/middle_right.png', middle)