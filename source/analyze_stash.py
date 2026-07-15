import cv2
import numpy as np
import easyocr
import os

def scan_stash_for_divines(screenshot_path, template_path):
    print("🚀 Starting ExileVision scan...")
    
    # 1. Load the images
    img_rgb = cv2.imread(screenshot_path)
    if img_rgb is None:
        print(f"❌ Error: Cannot find screenshot at {screenshot_path}")
        return
        
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"❌ Error: Cannot find template at {template_path}")
        return
        
    w, h = template.shape[::-1]
    
    # 2. Match the template against the screen
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.85  # Looking for an 85%+ perfect match
    loc = np.where(res >= threshold)
    
    # Initialize the local text reader engine
    reader = easyocr.Reader(['en'], gpu=False)
    
    detected_count = 0
    
    # Track coordinates to avoid duplicate detections on the exact same orb
    processed_points = []
    
    # 3. Process matches
    for pt in zip(*loc[::-1]):
        # Check if we already processed a point close to this one (avoids overlapping boxes)
        if any(abs(pt[0] - p[0]) < 10 and abs(pt[1] - p[1]) < 10 for p in processed_points):
            continue
        processed_points.append(pt)
        detected_count += 1
        
        # 4. Define the ROI (Region of Interest) where the text numbers sit.
        # Since the stack number is drawn slightly above/on the top half of the slot:
        crop_y1 = max(0, pt[1] - 25)
        crop_y2 = pt[1] + 20
        crop_x1 = max(0, pt[0] - 5)
        crop_x2 = pt[0] + w + 5
        
        roi = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # 5. Run OCR on the number area
        ocr_result = reader.readtext(roi, allowlist='0123456789')
        
        stack_size = "1" # Default to 1 if it finds the orb but can't read a number
        if ocr_result:
            stack_size = ocr_result[0][1]
            
        print(f"🎯 Found Divine Orb Stack #{detected_count} at X:{pt[0]} Y:{pt[1]} | Stack Size: {stack_size}")
        
        # Draw a visual box on the screen for your stream to see
        cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
        cv2.putText(img_rgb, f"Qty: {stack_size}", (pt[0], pt[1] - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save the debug image so you can show it on stream
    os.makedirs("debug", exist_ok=True)
    cv2.imwrite("debug/stash_scan_result.png", img_rgb)
    print(f"\n✅ Scan complete. Found {detected_count} Divine Orb slots.")
    print("Visual analysis saved to: debug/stash_scan_result.png")

if __name__ == "__main__":
    # Automatically find the latest screenshot you took using the hotkey script
    if os.path.exists("images") and os.listdir("images"):
        files = [os.path.join("images", f) for f in os.listdir("images") if f.endswith('.png')]
        if files:
            latest_screenshot = max(files, key=os.path.getctime)
            ##scan_stash_for_divines(latest_screenshot, "divine_template.png")
            scan_stash_for_divines(latest_screenshot, "exalted_template.png")
        else:
            print("No screenshots found in the 'images' folder. Take one using your hotkey script first!")
    else:
        print("Please run your capture_stash.py script first to generate the images directory.")