import os
import cv2

def slice_highlighted_zones(image_path, output_dir="debug_slots"):
    # Load the stash crop
    img = cv2.imread(image_path)
    if img is None:
        print(f"[-] Could not find {image_path}")
        return
        
    h, w, _ = img.shape
    os.makedirs(output_dir, exist_ok=True)
    
    # -----------------------------------------------------------------
    # Define exact normalized bounds (0.0 to 1.0) based on your new stripes
    # -----------------------------------------------------------------
    zones = {
        "Red_Cheap": {
            "bounds": (0.035, 0.320, 0.040, 0.235),  # left, right, top, bottom
            "rows": 2, "cols": 3,
            "items": [
                ["Transmutation", "Transmutation_II", "Transmutation_III"],
                ["Augmentation", "Augmentation_II", "Augmentation_III"]
            ]
        },
        "Orange_AltGold": {
            "bounds": (0.035, 0.320, 0.245, 0.340),
            "rows": 1, "cols": 3,
            "items": [["Alt_Gold", "Alt_Gold_II", "Alt_Gold_III"]]
        },
        "Yellow_Alchemy": {
            "bounds": (0.035, 0.320, 0.350, 0.440),
            "rows": 1, "cols": 3,
            "items": [["Alchemy", "Alchemy_II", "Alchemy_III"]]
        },
        "Green_Chaos": {
            "bounds": (0.035, 0.320, 0.450, 0.545),
            "rows": 1, "cols": 3,
            "items": [["Chaos", "Chaos_II", "Chaos_III"]]
        },
        "LightBlue_Annulment": {
            "bounds": (0.350, 0.655, 0.040, 0.140),
            "rows": 1, "cols": 3,
            "items": [["Chance", "Exalted", "Annulment"]]
        },
        "DarkBlue_Divine": {
            "bounds": (0.350, 0.655, 0.150, 0.235),
            "rows": 1, "cols": 3,
            "items": [["Regal", "Divine", "Mirror_Shard"]]
        }
    }

    print("[*] Slicing standard horizontal currency zones...")

    # Process all the uniform grid zones
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
                item_label = info["items"][r][c]
                x1 = bx1 + int(c * slot_w)
                x2 = bx1 + int((c + 1) * slot_w)
                y1 = by1 + int(r * slot_h)
                y2 = by1 + int((r + 1) * slot_h)
                
                cv2.imwrite(f"{output_dir}/{zone_name}_{item_label}.png", img[y1:y2, x1:x2])

    # -----------------------------------------------------------------
    # Purple Stripe (2 slots only, slightly shifted)
    # -----------------------------------------------------------------
    print("[*] Slicing Purple Big-Ticket zone...")
    
    p_y1, p_y2 = int(0.245 * h), int(0.335 * h)
    
    # Mirror of Kalandra Slot
    m_x1, m_x2 = int(0.405 * w), int(0.505 * w)
    cv2.imwrite(f"{output_dir}/Purple_Mirror_Of_Kalandra.png", img[p_y1:p_y2, m_x1:m_x2])
    
    # Hinecora's Lock Slot
    h_x1, h_x2 = int(0.515 * w), int(0.615 * w)
    cv2.imwrite(f"{output_dir}/Purple_Hinecoras_Lock.png", img[p_y1:p_y2, h_x1:h_x2])

    print(f"[+] Complete! All isolated items are inside the '{output_dir}' folder.")

if __name__ == "__main__":
    slice_highlighted_zones("temp_test_crop.png")