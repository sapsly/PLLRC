import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Let's look at the full frame with OCR - try to find ALL text in the frame
frame_idx = 5496  # This one had "X | 6" in top-right
frame_path = f'frames/race6_samples/frame_{frame_idx}.png'
img = cv2.imread(frame_path)
h, w = img.shape[:2]

print(f"Frame {frame_idx}: {w}x{h}")

# Run OCR on the full frame (downscaled for speed)
small = cv2.resize(img, (960, 540))
gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

print("\n--- Full frame OCR (thresholded) ---")
results = reader.readtext(thresh, detail=1, paragraph=False)
for bbox, text, conf in results:
    if conf > 0.2 and len(text.strip()) > 1:
        # Scale bbox back to original size
        scaled_bbox = [[int(p[0]*2), int(p[1]*2)] for p in bbox]
        print(f"  {text.strip()} (conf:{conf:.2f}) at {scaled_bbox}")

print("\n--- Full frame OCR (original) ---")
results = reader.readtext(gray, detail=1, paragraph=False)
for bbox, text, conf in results:
    if conf > 0.2 and len(text.strip()) > 1:
        scaled_bbox = [[int(p[0]*2), int(p[1]*2)] for p in bbox]
        print(f"  {text.strip()} (conf:{conf:.2f}) at {scaled_bbox}")

# Also try on specific regions upscaled
print("\n--- Upscaled regions ---")
regions = {
    'tl': img[20:200, 20:500],
    'tc': img[20:200, w//2-250:w//2+250],
    'tr': img[20:200, w-520:w-20],
    'ml': img[h//2-100:h//2+100, 20:500],
    'left_strip': img[100:h-100, 0:300],
    'right_strip': img[100:h-100, w-300:w],
}

for name, region in regions.items():
    if region.size == 0:
        continue
    # Upscale 3x
    up = cv2.resize(region, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    results = reader.readtext(thresh, detail=1, paragraph=False)
    for _, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            print(f"  {name}_thresh: \"{text.strip()}\" (conf:{conf:.2f})")
            break
    
    results = reader.readtext(gray, detail=1, paragraph=False)
    for _, text, conf in results:
        if conf > 0.2 and len(text.strip()) > 1:
            print(f"  {name}_orig: \"{text.strip()}\" (conf:{conf:.2f})")
            break