import cv2
import easyocr
import numpy as np
import os

reader = easyocr.Reader(['en'], gpu=False)

# Check race 6 at various points - it's the longest race (227s)
video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Race 6: {total_frames} frames, {fps:.1f} fps, {total_frames/fps:.1f}s")

# Sample frames at specific times
times = [10, 30, 60, 90, 120, 150, 180, 210]  # seconds
frame_indices = [int(t * fps) for t in times]

os.makedirs("frames/race6_samples", exist_ok=True)

for frame_idx in frame_indices:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"frames/race6_samples/frame_{frame_idx}.png", frame)
        
        h, w = frame.shape[:2]
        # Check multiple regions
        regions = {
            'tl': frame[20:200, 20:500],
            'tc': frame[20:200, w//2-250:w//2+250],
            'tr': frame[20:200, w-520:w-20],
            'ml': frame[h//2-100:h//2+100, 20:500],
        }
        
        print(f"\n=== Frame {frame_idx} (t={frame_idx/fps:.1f}s) ===")
        for name, region in regions.items():
            if region.size == 0:
                continue
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            for method_name, proc in [('orig', gray), ('thresh', thresh)]:
                results = reader.readtext(proc, detail=1, paragraph=False)
                for _, text, conf in results:
                    if conf > 0.3 and len(text.strip()) > 1:
                        print(f'  {name}_{method_name}: "{text.strip()}" (conf:{conf:.2f})')
                        break

cap.release()