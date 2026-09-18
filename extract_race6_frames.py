import cv2
import os
import easyocr
import numpy as np

# Extract frames every 1 second from race 6 (longest race)
video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
output_dir = r"frames\race6_dense"
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"FPS: {fps:.1f}, Total frames: {total_frames}, Duration: {total_frames/fps:.1f}s")

interval = int(fps * 1)  # Every 1 second
frame_idx = 0
saved = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % interval == 0:
        cv2.imwrite(os.path.join(output_dir, f"frame_{frame_idx:06d}.png"), frame)
        saved += 1
    frame_idx += 1

cap.release()
print(f"Saved {saved} frames")

# Now quickly test OCR on these to find race UI
reader = easyocr.Reader(['en'], gpu=False)

frames = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
print(f"\nTesting {len(frames)} frames for race UI...")

for frame in frames:
    frame_path = os.path.join(output_dir, frame)
    img = cv2.imread(frame_path)
    h, w = img.shape[:2]
    
    # Check multiple regions
    regions = {
        'top': img[30:180, 30:600],
        'top_left': img[30:180, 30:400],
        'top_center': img[30:180, w//2-200:w//2+200],
        'top_right': img[30:180, w-430:w-30],
        'mid_left': img[h//2-80:h//2+80, 30:400],
    }
    
    found_text = False
    for name, region in regions.items():
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        results = reader.readtext(thresh, detail=1, paragraph=False)
        texts = [f"'{t}'" for _, t, c in results if c > 0.4 and len(t.strip()) > 1]
        
        if texts:
            print(f"  {frame} [{name}]: {', '.join(texts[:3])}")
            found_text = True
            break
    
    if not found_text:
        # Try with original grayscale
        top_region = img[30:180, 30:600]
        gray = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(gray, detail=1, paragraph=False)
        texts = [f"'{t}'" for _, t, c in results if c > 0.4 and len(t.strip()) > 1]
        if texts:
            print(f"  {frame} [top_orig]: {', '.join(texts[:3])}")