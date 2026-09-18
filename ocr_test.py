import cv2
import os
import pytesseract

# Test OCR on a few frames
race1_dir = r"frames\race1"
frames = sorted([f for f in os.listdir(race1_dir) if f.endswith('.png') and not f.startswith('debug')])

for frame in frames[:3]:
    frame_path = os.path.join(race1_dir, frame)
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    # Try OCR on different regions
    # Top-left region (where strategy might be)
    top_left = img[50:150, 50:400]
    # Top-center
    top_center = img[50:150, w//2-200:w//2+200]
    # Top-right
    top_right = img[50:150, w-400:w-50]
    # Bottom region
    bottom = img[h-150:h-50, 50:400]
    
    regions = {
        'top_left': top_left,
        'top_center': top_center,
        'top_right': top_right,
        'bottom': bottom
    }
    
    print(f"\n=== {frame} ===")
    for name, region in regions.items():
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        # Enhance contrast
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        text = pytesseract.image_to_string(gray, config='--psm 7').strip()
        if text:
            print(f"  {name}: '{text}'")
        # Save for inspection
        cv2.imwrite(f"frames/ocr_{name}_{frame}", gray)