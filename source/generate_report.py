import os
import cv2
import re
import json
import numpy as np
from analyze_inventory import read_amount_from_crop 

def is_slot_empty(slot_img, threshold=30):
    """
    Calculates the average brightness of the slot.
    If it's below the threshold, it means the slot is just empty black space.
    """
    # Convert crop to grayscale
    gray = cv2.cvtColor(slot_img, cv2.COLOR_BGR2GRAY)
    # Calculate the average pixel value
    average_brightness = np.mean(gray)
    
    return average_brightness < threshold

def get_inventory_report(image_path="temp_test_crop.png"):
    img = cv2.imread(image_path)
    if img is None:
        print(f"[-] Could not find {image_path}.")
        return {}
        
    h, w, _ = img.shape
    report = {}
    
    # -----------------------------------------------------------------
    # Official PoE2 Currency Grid Zones (All mapped as 1-row strips)
    # -----------------------------------------------------------------
    zones = {
        # --- LEFT COLUMN ---
        "transmutation_zone": {
            "bounds": (0.035, 0.320, 0.040, 0.135),
            "rows": 1, "cols": 3,
            "items": [["orb-of-transmutation", "greater-orb-of-transmutation", "perfect-orb-of-transmutation"]]
        },
        "augmentation_zone": {
            "bounds": (0.035, 0.320, 0.140, 0.235),
            "rows": 1, "cols": 3,
            "items": [["orb-of-augmentation", "greater-orb-of-augmentation", "perfect-orb-of-augmentation"]]
        },
        "regal_zone": {
            "bounds": (0.035, 0.320, 0.245, 0.340),
            "rows": 1, "cols": 3,
            "items": [["regal-orb", "greater-regal-orb", "perfect-regal-orb"]]
        },
        "exalted_zone": {
            "bounds": (0.035, 0.320, 0.350, 0.440),
            "rows": 1, "cols": 3,
            "items": [["exalted-orb", "greater-exalted-orb", "perfect-exalted-orb"]]
        },
        "chaos_zone": {
            "bounds": (0.035, 0.320, 0.450, 0.545),
            "rows": 1, "cols": 3,
            "items": [["chaos-orb", "greater-chaos-orb", "perfect-chaos-orb"]]
        },
        
        # --- CENTER / RIGHT COLUMN ---
        "alchemy_chance_zone": {
            "bounds": (0.350, 0.655, 0.040, 0.140),
            "rows": 1, "cols": 3,
            "items": [["orb-of-alchemy", "vaal-orb", "orb-of-annulment"]]
        },
        "divine_fracturing_zone": {
            "bounds": (0.350, 0.655, 0.150, 0.235),
            "rows": 1, "cols": 3,
            "items": [["orb-of-chance", "fracturing-orb", "divine-orb"]]
        },
        "mirror_lock_zone": {
            "bounds": (0.350, 0.550, 0.245, 0.340), # Narrowed X range for 2 slots
            "rows": 1, "cols": 2,                   # Exact item count handling
            "items": [["mirror-of-kalandra", "hinekoras-lock"]]
        }
    }

    print(f"\n{'Database Item ID':<35} | {'Count':<10}")
    print("-" * 50)
    
    # Process all uniform strips cleanly
    for zone_name, info in zones.items():
        z_left, z_right, z_top, z_bottom = info["bounds"]
        rows, cols = info["rows"], info["cols"]
        
        bx1, bx2 = int(z_left * w), int(z_right * w)
        by1, by2 = int(z_top * h), int(z_bottom * h)
        
        block_w = bx2 - bx1
        block_h = by2 - by1
        
        slot_w = block_w / cols
        slot_h = block_h / rows
        
        for r in range(rows):
            for c in range(cols):
                # Grabs the exact kebab-case identifier string directly
                item_id = info['items'][r][c]
                
                x1 = bx1 + int(c * slot_w)
                x2 = bx1 + int((c + 1) * slot_w)
                y1 = by1 + int(r * slot_h)
                y2 = by1 + int((r + 1) * slot_h)
                
                slot_crop = img[y1:y2, x1:x2]
                
                if is_slot_empty(slot_crop):
                    count_val = 0
                else:
                    raw_output = read_amount_from_crop(slot_crop)
                    cleaned_digits = "".join(re.findall(r'\d+', str(raw_output)))
                    count_val = int(cleaned_digits) if cleaned_digits else 0
                
                # Assign count directly to the database item key
                report[item_id] = report.get(item_id, 0) + count_val
                print(f"{item_id:<35} | {count_val:<10}")

    print("-" * 50)
    return report

if __name__ == "__main__":
    inventory = get_inventory_report("temp_test_crop.png")
    
    report_file = "stash_report.json"
    with open(report_file, "w") as f:
        json.dump(inventory, f, indent=4)
    print(f"[+] Stash report saved successfully to '{report_file}'\n")