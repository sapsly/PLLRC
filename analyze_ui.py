import cv2
import os
import numpy as np

def analyze_frame(frame_path):
    img = cv2.imread(frame_path)
    if img is None:
        print(f"Failed to load {frame_path}")
        return
    
    h, w = img.shape[:2]
    print(f"\n{frame_path}: {w}x{h}")
    
    # Check different regions for UI elements
    # Top region (where strategy/pace/defend usually are)
    top_region = img[0:int(h*0.15), :]
    # Bottom region
    bottom_region = img[int(h*0.85):, :]
    # Left region
    left_region = img[:, 0:int(w*0.2)]
    # Right region
    right_region = img[:, int(w*0.8):]
    
    # Convert to grayscale and check for text-like patterns
    gray_top = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
    gray_bottom = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
    
    # Look for high contrast regions (potential text)
    _, thresh_top = cv2.threshold(gray_top, 200, 255, cv2.THRESH_BINARY)
    _, thresh_bottom = cv2.threshold(gray_bottom, 200, 255, cv2.THRESH_BINARY)
    
    top_white_pixels = np.sum(thresh_top == 255)
    bottom_white_pixels = np.sum(thresh_bottom == 255)
    
    print(f"  Top region white pixels: {top_white_pixels}")
    print(f"  Bottom region white pixels: {bottom_white_pixels}")
    
    # Save regions for visual inspection
    cv2.imwrite(f"frames/debug_top_{os.path.basename(frame_path)}", top_region)
    cv2.imwrite(f"frames/debug_bottom_{os.path.basename(frame_path)}", bottom_region)

# Analyze frames from race 1
race1_dir = r"frames\race1"
frames = sorted([f for f in os.listdir(race1_dir) if f.endswith('.png')])
for frame in frames[:5]:  # First 5 frames
    analyze_frame(os.path.join(race1_dir, frame))

print("\n" + "="*50)
print("Analyzing race 5 frames")
race5_dir = r"frames\race5"
frames = sorted([f for f in os.listdir(race5_dir) if f.endswith('.png')])
for frame in frames[:5]:
    analyze_frame(os.path.join(race5_dir, frame))

print("\n" + "="*50)
print("Analyzing race 6 frames")
race6_dir = r"frames\race6"
frames = sorted([f for f in os.listdir(race6_dir) if f.endswith('.png')])
for frame in frames[:5]:
    analyze_frame(os.path.join(race6_dir, frame))