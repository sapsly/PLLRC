import cv2
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

# Load ground truth and extract PIT region
gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
frame = cv2.imread(gt_path)

# Current localizer gives x=584-1910, so PIT is at right side
# From ground truth analysis, PIT label at x≈1650, value at x≈1700
# Row is y=832-952

pit_region = frame[832:952, 1650:1910]
cv2.imwrite('frames/ground_truth/pit_crop.png', pit_region)
print('PIT crop shape:', pit_region.shape)

# Test OCR on PIT region
gray = cv2.cvtColor(pit_region, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(up)
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

reader = easyocr.Reader(['en'], gpu=False)

for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
    results = reader.readtext(img, detail=1, paragraph=False)
    print('=== {} ==='.format(prep_name))
    for bbox, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            print('  "{}" (conf:{:.2f})'.format(text.strip(), conf))

cv2.imwrite('frames/ground_truth/pit_enhanced_4x.png', enhanced)
cv2.imwrite('frames/ground_truth/pit_thresh_4x.png', thresh)