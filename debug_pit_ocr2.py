import cv2
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

gt_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
frame = cv2.imread(gt_path)

# Let's check the full row to see where PIT actually is
row = frame[832:952, 584:1910]
cv2.imwrite('frames/ground_truth/full_row.png', row)

# Also save 4x upscaled for visual inspection
gray = cv2.cvtColor(row, cv2.COLOR_BGR2GRAY)
up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(up)
cv2.imwrite('frames/ground_truth/full_row_enhanced_4x.png', enhanced)

# Let's also try different PIT crops - maybe the x range is wrong
# Ground truth said PIT label at x≈1650, value at x≈1700
# Let's try wider crops
for x_start, x_end, name in [
    (1550, 1910, 'pit_wide'),
    (1600, 1910, 'pit_medium'),
    (1650, 1910, 'pit_narrow'),
    (1600, 1850, 'pit_label_area'),
    (1650, 1800, 'pit_value_area'),
]:
    crop = frame[832:952, x_start:x_end]
    cv2.imwrite('frames/ground_truth/{}.png'.format(name), crop)
    
    # Test OCR
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    gray_up = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY) if len(up.shape) == 3 else up
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray_up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print('\n=== {} (x={}-{}) ==='.format(name, x_start, x_end))
    for prep_name, img in [('enhanced', enhanced), ('thresh', thresh)]:
        results = reader.readtext(img, detail=1, paragraph=False)
        found = False
        for bbox, text, conf in reader.readtext(img, detail=1, paragraph=False):
            if conf > 0.15 and len(text.strip()) > 1:
                print('  {}: "{}" (conf:{:.2f})'.format(prep_name, text.strip(), conf))
                found = True
        if not found:
            print('  {}: (no text found)'.format(prep_name))