import cv2
import numpy as np
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

frames_to_check = [
    ('Race5_t30s', 'frames/ground_truth/Race5_t30s_pit.png'),
    ('Race6_t150s', 'frames/ground_truth/Race6_t150s_pit.png'),
    ('Race7_t70s', 'frames/ground_truth/Race7_t70s_pit.png'),
    ('Race8_t40s', 'frames/ground_truth/Race8_t40s_pit.png'),
    ('Race8_t50s', 'frames/ground_truth/Race8_t50s_pit.png'),
]

reader = easyocr.Reader(['en'], gpu=False)

for name, path in frames_to_check:
    img = cv2.imread(path)
    if img is None:
        print(name + ': NOT FOUND')
        continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    up = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(up)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print('\n=== ' + name + ' ===')
    for prep_name, img_prep in [('enhanced', enhanced), ('thresh', thresh)]:
        results = reader.readtext(img_prep, detail=1, paragraph=False)
        found = False
        for bbox, text, conf in results:
            if conf > 0.2 and len(text.strip()) > 1:
                if not found:
                    print('  ' + prep_name + ':')
                    found = True
                print('  "' + text.strip() + '" (conf:{:.2f})'.format(conf))
        if not found:
            print('  ' + prep_name + ': (no text found)')