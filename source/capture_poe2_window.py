import sys
import ctypes
import pygetwindow as gw
import mss
import numpy as np
import cv2
from PIL import Image

# 1. Force Windows to use true physical coordinates (DPI-Awareness)
if sys.platform == "win32":
    try:
        # For Windows 8.1 and 10+
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            # Fallback for older Windows versions
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            print("Could not set DPI awareness. Coordinate offsets might occur.")

def capture_window(window_title):
    # Find all windows matching the title
    all_windows = gw.getWindowsWithTitle(window_title)
    
    # Filter out VS Code or Python IDE windows that might contain the game title in their filenames
    windows = []
    for w in all_windows:
        title_lower = w.title.lower()
        if "visual studio" in title_lower or "vs code" in title_lower or ".py" in title_lower:
            continue
        if w.title.strip() == "": # Skip empty titles
            continue
        windows.append(w)

    if not windows:
        print(f"Error: Game window containing '{window_title}' not found!")
        print("Active windows found with similar names:")
        for w in all_windows:
            if w.title.strip():
                print(f" - {w.title}")
        return None
    
    # Use the first valid matching window
    window = windows[0]
    print(f"[+] Targeted window: '{window.title}'")
    
    # If minimized, restore it
    if window.isMinimized:
        window.restore()
    
    # Bring the window to the foreground
    try:
        window.activate()
    except Exception:
        # Avoid crashing if activation fails due to quick focus switching
        pass

    # Get window dimensions
    left, top, width, height = window.left, window.top, window.width, window.height
    
    # CRITICAL: We removed the `max(0, left)` and `max(0, top)` limits.
    # On multi-monitor setups, coordinates on secondary screens can legally be negative!
    print(f"Capturing region: Left={left}, Top={top}, Width={width}, Height={height}")

    # Use mss to capture the bounding box safely
    with mss.mss() as sct:
        monitor = {"top": top, "left": left, "width": width, "height": height}
        try:
            screenshot = sct.grab(monitor)
            # Convert mss format to standard OpenCV/Numpy BGR image
            img = np.array(screenshot)
            # mss returns BGRA, drop the alpha channel for OpenCV standard operations
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            print(f"Failed capturing with mss: {e}")
            return None

# --- Quick Test ---
if __name__ == "__main__":
    # Path of Exile 2 exact match
    game_title = "Path of Exile 2" 
    
    img = capture_window(game_title)
    if img is not None:
        cv2.imwrite("captured_test.png", img)
        print("Success! Image saved as captured_test.png")
    else:
        print("Capture failed.")