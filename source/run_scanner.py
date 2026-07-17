import cv2
import numpy as np
import pyautogui
import time
# This is where the import actually belongs!
from inventory_detector import parse_inventory_slot

START_X = 1031   
START_Y = 1905    
SLOT_SIZE = 60   
COLS = 12        
ROWS = 5         

def debug_crops():
    print("Taking screenshot in 3 seconds... switch to the game!")
    time.sleep(3)
    
    screenshot = pyautogui.screenshot()
    screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    # Let's crop just the very first slot (Row 0, Col 0)
    x1 = START_X
    y1 = START_Y
    x2 = x1 + SLOT_SIZE
    y2 = y1 + SLOT_SIZE
    
    slot_crop = screen_bgr[y1:y2, x1:x2]
    
    # Save it to your folder
    cv2.imwrite("debug_slot_0_0.png", slot_crop)
    print("Saved 'debug_slot_0_0.png'. Open this image to see if it is perfectly aligned!")

if __name__ == "__main__":
    debug_crops()

def capture_and_scan():
    print("Taking screenshot... Make sure your inventory is OPEN on screen!")
    screenshot = pyautogui.screenshot()
    screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    print("Scanning inventory grid...")
    for r in range(ROWS):
        for c in range(COLS):
            x1 = START_X + (c * SLOT_SIZE)
            y1 = START_Y + (r * SLOT_SIZE)
            x2 = x1 + SLOT_SIZE
            y2 = y1 + SLOT_SIZE
            
            slot_crop = screen_bgr[y1:y2, x1:x2]
            result = parse_inventory_slot(slot_crop)
            
            if result is not None:
                print(f"Slot [Row {r}, Col {c}]: Found {result['count']}x {result['item']}")

if __name__ == "__main__":
    print("Starting in 5 seconds... Switch to your game window!")
    time.sleep(5)
    capture_and_scan()