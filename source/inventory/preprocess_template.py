import cv2
import numpy as np

# ==========================================
# 1. INITIALIZATION & TEMPLATE LOADING
# ==========================================

def preprocess_number_template(image_path):
    """Loads a number template and converts it to pure black & white."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Warning: Could not load number template {image_path}")
        return None
    _, thresh = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    return thresh

# Load your clean number templates
digit_templates = {
    0: preprocess_number_template('template_numbers/zero.png'),
    1: preprocess_number_template('template_numbers/one.png'),
    2: preprocess_number_template('template_numbers/two.png'),
    3: preprocess_number_template('template_numbers/three.png'),
    4: preprocess_number_template('template_numbers/four.png'),
    5: preprocess_number_template('template_numbers/five.png'),
    6: preprocess_number_template('template_numbers/six.png'),
    7: preprocess_number_template('template_numbers/seven.png'),
    8: preprocess_number_template('template_numbers/eight.png'),
    9: preprocess_number_template('template_numbers/nine.png'),
}
# Filter out any missing files
digit_templates = {k: v for k, v in digit_templates.items() if v is not None}

# Load your currency templates (Keep these in color BGR)
# Add whatever filenames you have harvested so far!
currency_templates = {
    "Divine Orb": cv2.imread('template_currencies/divine.png'),
    "Chaos Orb": cv2.imread('template_currencies/chaos.png'),
    "Greater Chaos Orb": cv2.imread('template_currencies/greater_chaos.png'),
    "Perfect Chaos Orb": cv2.imread('template_currencies/perfect_chaos.png'),
    "Exalted Orb": cv2.imread('template_currencies/exalted.png'),
    "Greater Exalted Orb": cv2.imread('template_currencies/greater_exalted.png'),
    "Perfect Exalted Orb": cv2.imread('template_currencies/perfect_exalted.png'),
    "Regal Orb": cv2.imread('template_currencies/regal.png'),
    "Greater Regal Orb": cv2.imread('template_currencies/greater_regal.png'),
    "Perfect Regal Orb": cv2.imread('template_currencies/perfect_regal.png'),
    # Mirror and Lock are skipped safely here! (the real reason is because I'm too poor to afford them, but you can add them if you have the templates)
}
currency_templates = {k: v for k, v in currency_templates.items() if v is not None}


# ==========================================
# 2. CORE DETECTION FUNCTIONS
# ==========================================

def identify_currency(slot_crop):
    """
    Compares the full slot crop against your currency portfolio.
    If it doesn't match anything but contains an item, it catches the mirror/lock.
    """
    best_match = None
    best_val = 0.0
    threshold = 0.75 # Adjust based on your crop precision
    
    for name, template in currency_templates.items():
        res = cv2.matchTemplate(slot_crop, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        
        if max_val > best_val:
            best_val = max_val
            best_match = name
            
    if best_val >= threshold:
        return best_match
        
    # --- Fallback for Mirror / Lock / Unregistered expensive items ---
    # Check if the slot is empty or actually has an item by looking at image variance
    gray_slot = cv2.cvtColor(slot_crop, cv2.COLOR_BGR2GRAY)
    if np.std(gray_slot) > 15: # An empty dark grid slot has very low color variance
        return "Unknown / High-Value Currency"
        
    return "Empty"


def scan_stack_size(slot_crop):
    """
    Isolates the text zone in the upper left, binarizes it, 
    and reads the digits from left to right.
    """
    # Crop to where the number typically renders (top-left 32x32 area)
    # Adjust slicing limits if your inventory grid tiles are larger/smaller
    text_zone = slot_crop[0:32, 0:32] 
    
    gray_zone = cv2.cvtColor(text_zone, cv2.COLOR_BGR2GRAY)
    _, thresh_zone = cv2.threshold(gray_zone, 120, 255, cv2.THRESH_BINARY)
    
    detected_digits = []
    
    for digit, template in digit_templates.items():
        res = cv2.matchTemplate(thresh_zone, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.85) # High confidence threshold for B&W shapes
        
        for pt in zip(*loc[::-1]):
            detected_digits.append((pt[0], digit))
            
    # Sort positions left-to-right (crucial for double digits like 10, 20)
    detected_digits.sort(key=lambda x: x[0])
    
    final_digits = []
    last_x = -10
    for x, digit in detected_digits:
        if x - last_x > 3: # Skip duplicate overlap ticks
            final_digits.append(str(digit))
            last_x = x
            
    if not final_digits:
        return 1 # If the slot has an item but no visible text, it means stack size is 1
        
    return int("".join(final_digits))


# ==========================================
# 3. RUNNING THE INVENTORY PARSER
# ==========================================

def parse_inventory_slot(slot_image):
    """
    Processes a single individual slot image.
    """
    item_type = identify_currency(slot_image)
    
    if item_type == "Empty":
        return None
        
    stack_count = scan_stack_size(slot_image)
    return {"item": item_type, "count": stack_count}

# Example Usage:
# If you have a 60x60 cropped image snippet of a specific slot:
# result = parse_inventory_slot(my_slot_crop)
# print(result) -> {"item": "Divine Orb", "count": 10}