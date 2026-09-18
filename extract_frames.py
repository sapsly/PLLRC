import cv2
import os

video_path = r"Training\PLLRC_Videos\Race_001_06-09-2026.mp4"
output_dir = r"frames\race1"
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"FPS: {fps}, Total frames: {total_frames}, Duration: {total_frames/fps:.1f}s")

# Extract every 5 seconds
interval = int(fps * 5)
frame_idx = 0
saved = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % interval == 0:
        cv2.imwrite(os.path.join(output_dir, f"frame_{frame_idx:06d}.png"), frame)
        saved += 1
        print(f"Saved frame {frame_idx} (t={frame_idx/fps:.1f}s)")
    frame_idx += 1

cap.release()
print(f"Saved {saved} frames")