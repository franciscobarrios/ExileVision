import os
import cv2
import numpy as np
import easyocr

print("Initializing OCR Reader...")
reader = easyocr.Reader(['en'], gpu=False)

crops_folder = "debug_crops"
processed_folder = "debug_processed"

if not os.path.exists(crops_folder):
    print(f"Error: Could not find the folder '{crops_folder}'.")
    exit()

if not os.path.exists(processed_folder):
    os.makedirs(processed_folder)

print(f"Processing and scanning game icons...\n")
print("-" * 75)

for filename in os.listdir(crops_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        img_path = os.path.join(crops_folder, filename)
        
        # 1. Load image
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        # 2. Add a solid black border (gives OCR space to recognize characters near the edge)
        padded = cv2.copyMakeBorder(
            img, 
            top=10, bottom=10, left=10, right=10, 
            borderType=cv2.BORDER_CONSTANT, 
            value=[0, 0, 0]
        )
        
        # 3. Upscale 4x using cubic interpolation to make text strokes thicker and smoother
        upscaled = cv2.resize(padded, (0, 0), fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        
        # 4. Convert to Grayscale
        gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
        
        # 5. Bilateral Filter: Smooths background textures (hair/metal details) while keeping sharp text edges
        filtered = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        
        # 6. Use your proven threshold value of 149!
        _, thresh = cv2.threshold(filtered, 149, 255, cv2.THRESH_BINARY)
        
        # 7. Apply a strict "Top-Left" Text Zone Mask
        # This keeps 72% of the width (safe for 4-digit numbers) 
        # and only the top 48% of the height (deletes all noise below the numbers)
        h_thresh, w_thresh = thresh.shape
        text_zone_h = int(h_thresh * 0.59)
        text_zone_w = int(w_thresh * 0.7)
        
        # Create a solid black canvas and copy only our strict text zone over
        cleaned_zone = np.zeros_like(thresh)
        cleaned_zone[0:text_zone_h, 0:text_zone_w] = thresh[0:text_zone_h, 0:text_zone_w]
        
        # 8. Clean up tiny floating white specs
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(cleaned_zone, cv2.MORPH_OPEN, kernel)
        
        # Save the debug image so you can visually verify
        processed_path = os.path.join(processed_folder, f"proc_{filename}")
        cv2.imwrite(processed_path, cleaned)
        
        # 9. OCR Recognition
        results = reader.readtext(
            cleaned, 
            allowlist="0123456789", 
            detail=0,
            paragraph=False,
            text_threshold=0.3,
            low_text=0.3,
            link_threshold=0.3
        )
        
        detected_text = results[0] if results else "No digits found"
        print(f"File: {filename:<30} | Detected Number: {detected_text}")

print("-" * 75)
print(f"Done! Check the '{processed_folder}' folder to see if the '6' and '137' are isolated.")