import cv2
import os
import easyocr

reader = easyocr.Reader(['en'], gpu=False)

# Test OCR on a few frames from different races
for race_num in [1, 5, 6, 7]:
    race_dir = f"frames/race{race_num}"
    frames = sorted([f for f in os.listdir(race_dir) if f.endswith('.png') and not f.startswith('debug') and not f.startswith('ocr')])
    
    print(f"\n{'='*60}")
    print(f"RACE {race_num}")
    print(f"{'='*60}")
    
    for frame in frames[:3]:
        frame_path = os.path.join(race_dir, frame)
        img = cv2.imread(frame_path)
        h, w = img.shape[:2]
        
        print(f"\n--- {frame} ({w}x{h}) ---")
        
        # Define regions to test (relative coordinates)
        regions = {
            'top_left': img[30:180, 30:450],
            'top_center': img[30:180, w//2-250:w//2+250],
            'top_right': img[30:180, w-480:w-30],
            'mid_left': img[h//2-100:h//2+50, 30:450],
            'bottom_left': img[h-200:h-50, 30:450],
            'bottom_center': img[h-200:h-50, w//2-250:w//2+250],
        }
        
        for name, region in regions.items():
            if region.size == 0:
                continue
            # Preprocess: grayscale, enhance contrast
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            # Try both original and thresholded
            for suffix, proc_img in [('orig', gray), ('thresh', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])]:
                results = reader.readtext(proc_img, detail=1, paragraph=False)
                if results:
                    for bbox, text, conf in results:
                        if conf > 0.3 and len(text.strip()) > 1:
                            print(f"  {name}_{suffix}: '{text.strip()}' (conf: {conf:.2f})")
                            break