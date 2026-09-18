import cv2
import os
import easyocr
import numpy as np

reader = easyocr.Reader(['en'], gpu=False)

# Check race 1 more carefully - look for transitions
video_path = r"Training\PLLRC_Videos\Race_001_06-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Race 1: {total_frames} frames, {fps:.1f} fps, {total_frames/fps:.1f}s")

# Sample frames throughout the video, check for visual changes
prev_hist = None
changes = []

for frame_idx in range(0, total_frames, int(fps * 2)):  # Every 2 seconds
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret:
        break
    
    # Compute histogram of top region (where UI changes would be)
    top = frame[30:180, 30:600]
    hsv = cv2.cvtColor(top, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    
    if prev_hist is not None:
        diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
        if diff > 0.3:  # Significant change
            changes.append((frame_idx, diff))
            print(f"  Change at frame {frame_idx} (t={frame_idx/fps:.1f}s): diff={diff:.3f}")
    
    prev_hist = hist

cap.release()
print(f"\nTotal significant changes: {len(changes)}")
for idx, diff in changes:
    print(f"  Frame {idx} (t={idx/fps:.1f}s): diff={diff:.3f}")

# Now check frames around changes for race UI
if changes:
    for change_idx, _ in changes[:5]:  # Check first 5 changes
        for offset in [-30, 0, 30, 60, 90, 120]:
            check_idx = change_idx + offset
            if 0 <= check_idx < total_frames:
                cap = cv2.VideoCapture(video_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, check_idx)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    # Check multiple regions
                    h, w = frame.shape[:2]
                    regions = {
                        'top_left': frame[30:180, 30:400],
                        'top_center': frame[30:180, w//2-200:w//2+200],
                        'mid_left': frame[h//2-80:h//2+80, 30:400],
                        'bottom_left': frame[h-180:h-30, 30:400],
                    }
                    
                    for name, region in regions.items():
                        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        results = reader.readtext(thresh, detail=1, paragraph=False)
                        for _, t, c in results:
                            if c > 0.4 and len(t.strip()) > 1:
                                print(f"    Frame {check_idx} [{name}]: '{t}' (conf:{c:.2f})")
                                break