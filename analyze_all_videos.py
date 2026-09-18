import cv2
import os

# Quick visual analysis of all videos - find transitions
video_files = [
    r"Training\PLLRC_Videos\Race_001_06-09-2026.mp4",
    r"Training\PLLRC_Videos\Race_005_07-09-2026.mp4",
    r"Training\PLLRC_Videos\Race_006_07-09-2026.mp4",
    r"Training\PLLRC_Videos\Race_007_07-09-2026.mp4",
    r"Training\PLLRC_Videos\Race_014_07-09-2026.mp4",
    r"Training\PLLRC_Videos\Race_015_08-09-2026.mp4",
    r"Training\PLLRC_Videos\Race_016_08-09-2026.mp4",
]

for video_path in video_files:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    race_name = os.path.basename(video_path)
    print(f"\n{race_name}: {total_frames} frames, {fps:.1f} fps, {duration:.1f}s")
    
    # Sample frames and check color histogram of full frame
    prev_hist = None
    changes = []
    
    sample_interval = max(1, int(fps * 2))  # Every 2 seconds
    for frame_idx in range(0, total_frames, sample_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        
        # Full frame histogram
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        if prev_hist is not None:
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
            if diff > 0.25:  # Significant visual change
                changes.append((frame_idx, diff))
        
        prev_hist = hist
    
    cap.release()
    
    if changes:
        print(f"  Visual changes at: {[(f, f/fps, f'{d:.3f}') for f, d in changes]}")
    else:
        print(f"  No significant visual changes detected (static content)")

print("\n=== Analysis complete ===")