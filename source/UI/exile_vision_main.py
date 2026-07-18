import cv2
import numpy as np
import easyocr
import requests
import os
import time
import keyboard
from PIL import ImageGrab

# --- CONFIGURATION ---
TRIGGER_HOTKEY = "ctrl+alt+s"
LEAGUE = "Runes of Aldur"
##TEMPLATE_PATH = "divine_template.png"
TEMPLATE_PATH = "exalted_template.png"

# Initialize EasyOCR engine globally so it doesn't reload on every hotkey press
print("Initializing local OCR engine...")
reader = easyocr.Reader(['en'], gpu=False)

def fetch_live_divine_price():
    """Fetches the current live Chaos Orb value of a Divine Orb from poe.ninja"""
    url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={LEAGUE}&type=Currency"
    headers = {'User-Agent': 'Mozilla/5.0 ExileVision/1.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            lines = data.get('lines', [])
            for line in lines:
                if line.get('currencyTypeName') == 'Divine Orb':
                    # poe.ninja tracks currency values relative to Chaos Orbs
                    return line.get('chaosEquivalent', 0.0)
    except Exception as e:
        print(f"⚠️ Could not update live price data: {e}")
    
    # Return a fallback price if API is down or league has just launched
    return 120.0 

def run_full_analysis():
    print("\n==================================================")
    print("📸 [ExileVision] Triggered! Snapping virtual workspace...")
    
    # 1. Capture the multi-monitor canvas setup
    try:
        screenshot = ImageGrab.grab(all_screens=True)
        img_rgb = np.array(screenshot)
        img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"❌ Screen capture initialization failed: {e}")
        return

    # 2. Check for the Divine Template
    template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"❌ Template missing! Place your clean crop at: {TEMPLATE_PATH}")
        return
    w, h = template.shape[::-1]

    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= 0.85)
    
    total_divines = 0
    processed_points = []
    
    # 3. OCR and Counting Loop
    for pt in zip(*loc[::-1]):
        if any(abs(pt[0] - p[0]) < 10 and abs(pt[1] - p[1]) < 10 for p in processed_points):
            continue
        processed_points.append(pt)
        
        # Crop the boundary text field sitting above the matched asset block
        crop_y1 = max(0, pt[1] - 25)
        crop_y2 = pt[1] + 20
        crop_x1 = max(0, pt[0] - 5)
        crop_x2 = pt[0] + w + 5
        
        roi = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]
        ocr_result = reader.readtext(roi, allowlist='0123456789')
        
        stack_size = 1
        if ocr_result:
            try:
                stack_size = int(ocr_result[0][1])
            except ValueError:
                stack_size = 1
                
        total_divines += stack_size

    # 4. Fetch Market Pricing and Output Results
    if total_divines > 0:
        print(f"📊 Found a total of {total_divines} Divine Orbs on screen.")
        print("Fetching latest poe.ninja market evaluations...")
        divine_to_chaos_rate = fetch_live_divine_price()
        
        total_value_chaos = total_divines * divine_to_chaos_rate
        
        print("\n--- 💰 live stash evaluation summary ---")
        print(f" League:         {LEAGUE}")
        print(f" Total Holdings: {total_divines}x Divine Orbs")
        print(f" Market Rate:    1 Divine = {divine_to_chaos_rate:.1f} Chaos")
        print(f" Total Value:    {total_value_chaos:.1f} Chaos Orbs")
        print("----------------------------------------")
    else:
        print("🔍 Scan finished: No Divine Orb patterns detected on the active monitors.")

def main():
    print("=== ExileVision Master Engine Online ===")
    print(f"League Focus: {LEAGUE}")
    print(f"Press '{TRIGGER_HOTKEY}' while tabbed into the game to evaluate net worth.")
    print("Press Ctrl+C directly inside this terminal to close the application.")
    
    keyboard.add_hotkey(TRIGGER_HOTKEY, run_full_analysis)
    keyboard.wait()

if __name__ == "__main__":
    main()