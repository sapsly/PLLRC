import cv2
import os

# Extract frames from race 6 around the "LIVE RACE" moments
video_path = r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

# Frames where LIVE RACE was detected: 5496, 7695
# Also check around the visual changes: 876, 949, 2482, 5475, 5548, 8103
key_frames = [876, 949, 2482, 5475, 5496, 5548, 7695, 8103]

os.makedirs("frames/race6_key", exist_ok=True)

for frame_idx in key_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"frames/race6_key/frame_{frame_idx}.png", frame)
        print(f"Saved frame {frame_idx} (t={frame_idx/fps:.1f}s)")

cap.release()