import cv2
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

# Check t=90s frame full lower region
frame = cv2.imread('frames/recovery/test_t90s.png')
h, w = frame.shape[:2]

# Search full lower region
search_region = frame[700:1080, 0:w]
gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(up)

results = reader.readtext(enhanced, detail=1, paragraph=False)
print("=== Full lower region OCR (t=90s) ===")
for bbox, text, conf in results:
    if conf > 0.25 and len(text.strip()) > 1:
        x_coords = [int(p[0] / 3) for p in bbox]
        y_coords = [int(p[1] / 3) + 700 for p in bbox]
        x_center = sum(x_coords) / 4
        y_center = sum(y_coords) / 4
        print('  "{}" (conf:{:.2f}) at x={:.0f}, y={:.0f}'.format(text.strip(), conf, x_center, y_center))