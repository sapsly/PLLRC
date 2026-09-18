import cv2
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

# Test just one region - bottom_left from race 6 t=150s
region = cv2.imread('frames/key_regions/bottom_left.png')
if region is None:
    print('File not found')
    exit()

gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(up)
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

for prep_name, img in [('e', enhanced), ('t', thresh)]:
    results = reader.readtext(img, detail=1, paragraph=False)
    for _, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            print(prep_name + ': "' + text.strip() + '" (conf:' + "{:.2f})".format(conf))