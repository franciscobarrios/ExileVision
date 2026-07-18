import cv2
import numpy as np

# Load your clean number templates
def preprocess_number_template(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    _, thresh = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    return thresh

digit_templates = {
    0: preprocess_number_template('number_templates/zero.png'),
    1: preprocess_number_template('number_templates/one.png'),
    2: preprocess_number_template('number_templates/two.png'),
    3: preprocess_number_template('number_templates/three.png'),
    4: preprocess_number_template('number_templates/four.png'),
    5: preprocess_number_template('number_templates/five.png'),
    6: preprocess_number_template('number_templates/six.png'),
    7: preprocess_number_template('number_templates/seven.png'),
    8: preprocess_number_template('number_templates/eight.png'),
    9: preprocess_number_template('number_templates/nine.png'),
}
digit_templates = {k: v for k, v in digit_templates.items() if v is not None}

currency_templates = {
    "Divine Orb": cv2.imread('currency_templates/divine.png'),
    "Exalted Orb": cv2.imread('currency_templates/exalted.png'),
    "Greater Exalted Orb": cv2.imread('currency_templates/greater_exalted.png'),
    "Perfect Exalted Orb": cv2.imread('currency_templates/perfect_exalted.png'),
    "Chaos Orb": cv2.imread('currency_templates/chaos.png'),
    "Greater Chaos Orb": cv2.imread('currency_templates/greater_chaos.png'),
    "Perfect Chaos Orb": cv2.imread('currency_templates/perfect_chaos.png'),
    "Annulment": cv2.imread('currency_templates/annulment.png'),
    "Fracturing Orb": cv2.imread('currency_templates/fracturing.png'),
    "Regal Orb": cv2.imread('currency_templates/regal.png'),
    "Greater Regal Orb": cv2.imread('currency_templates/greater_regal.png'),
    "Perfect Regal Orb": cv2.imread('currency_templates/perfect_regal.png'),
}
currency_templates = {k: v for k, v in currency_templates.items() if v is not None}

def identify_currency(slot_crop):
    best_match = None
    best_val = 0.0
    threshold = 0.75
    
    for name, template in currency_templates.items():
        res = cv2.matchTemplate(slot_crop, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val
            best_match = name
            
    if best_val >= threshold:
        return best_match
        
    gray_slot = cv2.cvtColor(slot_crop, cv2.COLOR_BGR2GRAY)
    if np.std(gray_slot) > 15:
        return "Unknown / High-Value Currency"
    return "Empty"

def scan_stack_size(slot_crop):
    text_zone = slot_crop[0:32, 0:32] 
    gray_zone = cv2.cvtColor(text_zone, cv2.COLOR_BGR2GRAY)
    _, thresh_zone = cv2.threshold(gray_zone, 120, 255, cv2.THRESH_BINARY)
    
    detected_digits = []
    for digit, template in digit_templates.items():
        res = cv2.matchTemplate(thresh_zone, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.85)
        for pt in zip(*loc[::-1]):
            detected_digits.append((pt[0], digit))
            
    detected_digits.sort(key=lambda x: x[0])
    final_digits = []
    last_x = -10
    for x, digit in detected_digits:
        if x - last_x > 3:
            final_digits.append(str(digit))
            last_x = x
            
    if not final_digits:
        return 1
    return int("".join(final_digits))

def parse_inventory_slot(slot_image):
    item_type = identify_currency(slot_image)
    if item_type == "Empty":
        return None
    stack_count = scan_stack_size(slot_image)
    return {"item": item_type, "count": stack_count}