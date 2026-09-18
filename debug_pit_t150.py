import cv2
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

frame = cv2.imread('frames/recovery/test_t150s.png')
if frame is None:
    print('Frame not found')
    exit()

right = frame[832:952, 1600:1910]
gray = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(up)
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

reader = easyocr.Reader(['en'], gpu=False)

for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
    results = reader.readtext(img, detail=1, paragraph=False)
    print('=== {} ==='.format(prep_name))
    for bbox, text, conf in results:
        if conf > 0.15 and len(text.strip()) > 1:
            print('  "{}" (conf:{:.2f})'.format(text.strip(), conf))

cv2.imwrite('frames/ground_truth/pit_t150s_enhanced_4x.png', enhanced)
cv2.imwrite('frames/ground_truth/pit_t150s_thresh_4x.png', thresh)