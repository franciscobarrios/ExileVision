import os
import cv2
import re

# Assuming your local AI function is named read_amount_from_crop 
# Adjust this import to match where your OCR function is defined in your project
from analyze_inventory import read_amount_from_crop 

def test_specific_slots():
    # Path to the debug slots directory
    slots_dir = "debug_slots"
    
    # The two specific target files you requested
    target_files = [
        "DarkBlue_Divine_Mirror_Shard.png",
        "LightBlue_Annulment_Annulment.png"
    ]
    
    print("[*] Starting isolated slot OCR test...\n" + "="*40)
    
    for filename in target_files:
        file_path = os.path.join(slots_dir, filename)
        
        # Check if the file exists before attempting to process
        if not os.path.exists(file_path):
            print(f"[-] File not found: {file_path}")
            print(f"    Please ensure you ran 'slice_grid.py' first.")
            continue
            
        # Load the image slot slice
        slot_img = cv2.imread(file_path)
        
        if slot_img is not None:
            # Run the local AI engine on the individual slot crop
            raw_output = read_amount_from_crop(slot_img)
            
            # Clean up the output using regex to keep only digits
            # (Matches how your original script stripped text out)
            cleaned_digits = "".join(re.findall(r'\d+', str(raw_output)))
            
            print(f"[+] File: {filename}")
            print(f"    -> Raw AI Output: '{raw_output}'")
            print(f"    -> Cleaned Count: {cleaned_digits if cleaned_digits else '0 (No numbers detected)'}")
            print("-" * 40)
        else:
            print(f"[-] Error: Could not read image matrix for {filename}")

if __name__ == "__main__":
    test_specific_slots()