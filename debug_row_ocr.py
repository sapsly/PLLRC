import cv2
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
frame = cv2.imread(gt_path)

# Use the same region as the pipeline
y_top, y_bottom = 833, 916
x_left, x_right = 774, 1248
row_img = frame[y_top:y_bottom, x_left:x_right]

cv2.imwrite('frames/ground_truth/row_crop.png', row_img)

gray = cv2.cvtColor(row_img, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(up)
_, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

reader = easyocr.Reader(['en'], gpu=False)

for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
    print('=== {} ==='.format(prep_name))
    results = reader.readtext(img, detail=1, paragraph=False)
    for bbox, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            print('  "{}" (conf:{:.2f})'.format(text.strip(), conf))

cv2.imwrite('frames/ground_truth/row_enhanced_4x.png', enhanced)
cv2.imwrite('frames/ground_truth/row_thresh_4x.png', thresh)