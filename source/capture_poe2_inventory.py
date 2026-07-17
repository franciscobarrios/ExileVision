import pygetwindow as gw
import cv2
import time
import numpy as np
import mss

def capture_poe2_inventory():
    # 1. Search for any window matching the title
    matching_windows = gw.getWindowsWithTitle('Path of Exile 2')
    
    # 2. Safe check: If the list is empty, exit gracefully
    if not matching_windows:
        print("[-] Path of Exile 2 is not currently running.")
        return None
        
    # 3. Target the active window
    win = matching_windows[0]

    # 4. Bring the window to the foreground if it isn't already
    try:
        if not win.isActive:
            win.activate()
            # Give Windows a split second to focus and render the window frame
            time.sleep(0.1) 
    except Exception as e:
        print(f"[!] Warning: Could not force focus on the window: {e}")

    # 5. Take the screenshot of the specific window boundaries using MSS
    try:        
        # Define the bounding box dictionary for mss
        monitor_region = {
            "top": win.top, 
            "left": win.left, 
            "width": win.width, 
            "height": win.height
        }
        
        with mss.mss() as sct:
            # Grab the raw pixels from the direct GPU/DWM system
            screenshot = sct.grab(monitor_region)
            
            # Convert the raw mss bytes into a NumPy array for OpenCV
            # Note: mss captures in BGRA format by default
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR to drop the alpha channel for clean OpenCV savings
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame

    except Exception as e:
        print(f"[-] Failed to capture screenshot: {e}")
        return None

# --- Quick Test ---
if __name__ == "__main__":
    print("[*] Waiting 3 seconds... switch to your game window!")
    time.sleep(3)
    img = capture_poe2_inventory()
    if img is not None:
        # Save it locally to verify what it captured
        cv2.imwrite("captured_poe2.png", img)
        print("[+] Saved capture as 'captured_poe2.png' successfully!")