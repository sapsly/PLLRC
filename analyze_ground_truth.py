import cv2
import numpy as np
import os

# Load the ground truth screenshot
img_path = r'Training\PLLRC_Screenshots\Screenshot 2026-09-08 21.24.37.png'
img = cv2.imread(img_path)
if img is None:
    print("Failed to load image")
    exit()

h, w = img.shape[:2]
print("Ground truth screenshot: {}x{}".format(w, h))

# Save full image for reference
os.makedirs('frames/ground_truth', exist_ok=True)
cv2.imwrite('frames/ground_truth/full_gt.png', img)

# The user mentioned "lower race-control area" - let's examine the bottom portion
bottom = img[800:1080, 0:1920]
bottom_hsv = cv2.cvtColor(bottom, cv2.COLOR_BGR2HSV)

for cname, ranges in [
    ('green', [(35,50,50),(85,255,255)]),
    ('red', [(0,50,50),(10,255,255)]),
    ('yellow', [(15,50,50),(35,255,255)]),
    ('blue', [(90,50,50),(130,255,255)]),
    ('orange', [(10,50,50),(25,255,255)]),
    ('white', [(0,0,200),(180,30,255)]),
    ('cyan', [(85,50,50),(95,255,255)]),
]:
    if cname == 'red':
        mask1 = cv2.inRange(bottom_hsv, ranges[0], ranges[1])
        mask2 = cv2.inRange(bottom_hsv, (170,50,50), (180,255,255))
        mask = mask1 | mask2
    else:
        mask = cv2.inRange(bottom_hsv, ranges[0], ranges[1])
    pct = np.sum(mask > 0) / mask.size * 100
    if pct > 0.5:
        print("  Bottom {}: {:.1f}%".format(cname, pct))

# Save bottom region for inspection
cv2.imwrite('frames/ground_truth/bottom_800_1080.png', bottom)
bottom_mid = img[700:900, 0:1920]
cv2.imwrite('frames/ground_truth/bottom_700_900.png', bottom_mid)
bottom_300 = img[780:1080, 0:1920]
cv2.imwrite('frames/ground_truth/bottom_300.png', bottom_300)

# Horizontal band analysis
print("\n=== HORIZONTAL BAND ANALYSIS (bottom 300px) ===")
for y_start in range(780, 1080, 20):
    band = img[y_start:y_start+20, 0:1920]
    band_hsv = cv2.cvtColor(band, cv2.COLOR_BGR2HSV)
    
    for cname, ranges in [
        ('green', [(35,50,50),(85,255,255)]),
        ('red', [(0,50,50),(10,255,255)]),
        ('yellow', [(15,50,50),(35,255,255)]),
        ('blue', [(90,50,50),(130,255,255)]),
        ('orange', [(10,50,50),(25,255,255)]),
        ('white', [(0,0,200),(180,30,255)]),
    ]:
        if cname == 'red':
            mask1 = cv2.inRange(band_hsv, ranges[0], ranges[1])
            mask2 = cv2.inRange(band_hsv, (170,50,50), (180,255,255))
            mask = mask1 | mask2
        else:
            mask = cv2.inRange(band_hsv, ranges[0], ranges[1])
        pct = np.sum(mask > 0) / mask.size * 100
        if pct > 1:
            print("  y={}-{}: {}={:.1f}%".format(y_start, y_start+20, cname, pct))

# Edge detection for UI boundaries
print("\n=== EDGE DETECTION FOR UI BOUNDARIES ===")
gray_bottom = cv2.cvtColor(bottom_300, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray_bottom, 50, 150)
cv2.imwrite('frames/ground_truth/bottom_edges.png', edges)

contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print("Found {} contours in bottom region".format(len(contours)))

ui_elements = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    if 200 < area < 50000:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect = w / h if h > 0 else 0
        if 0.2 < aspect < 10:
            ui_elements.append((x, y, w, h, area, aspect))

ui_elements.sort(key=lambda e: (e[1], e[0]))

print("\nUI-like elements ({}):".format(len(ui_elements)))
for i, (x, y, w, h, area, aspect) in enumerate(ui_elements[:30]):
    abs_y = y + 780
    print("  {}: x={}, y={}, w={}, h={}, area={:.0f}, aspect={:.2f}".format(i, x, abs_y, w, h, area, aspect))

# Control area
control_area = img[850:1000, 0:1920]
cv2.imwrite('frames/ground_truth/control_area.png', control_area)

# 4x upscaled for text reading
for name, region in [('full', img), ('bottom_300', bottom_300), ('control_area', control_area)]:
    up = cv2.resize(region, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('frames/ground_truth/{}_4x.png'.format(name), up)
    print("Saved {}_4x.png".format(name))

# Specific region analysis
print("\n=== SPECIFIC REGION ANALYSIS ===")
for x_start in range(0, 1920, 200):
    region = control_area[:, x_start:x_start+200]
    if region.size == 0:
        continue
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)
    mean_val = np.mean(gray)
    if contrast > 30 or mean_val > 200 or mean_val < 50:
        print("  x={}-{}: mean={:.1f}, std={:.1f}".format(x_start, x_start+200, mean_val, contrast))