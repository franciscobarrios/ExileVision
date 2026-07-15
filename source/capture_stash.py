import keyboard
from PIL import ImageGrab
import os
import time

# Define the hotkey combo to trigger the capture
TRIGGER_HOTKEY = "ctrl+alt+s"

def capture_screen_region():
    print("\n[ExileVision] Hotkey detected! Capturing screen...")
    
    try:
        # Take a full screenshot of your main monitor
        # In the future, we can restrict these coordinates to just your stash tab box
        # screenshot = ImageGrab.grab()
        screenshot = ImageGrab.grab(all_screens=True)
        
        # Ensure an 'images' directory exists to store the captures
        os.makedirs("images", exist_ok=True)
        
        # Generate a clean, time-stamped filename
        filename = f"images/stash_{int(time.time())}.png"
        
        # Save the image file
        screenshot.save(filename)
        print(f"📸 Stash captured successfully saved to: {filename}")
        print("Ready for next capture. Press Ctrl+C in this terminal to exit.")
        
    except Exception as e:
        print(f"❌ Failed to capture screen: {str(e)}")

def main():
    print("=== ExileVision Screen Capture Module ===")
    print(f"Running in background... Press '{TRIGGER_HOTKEY}' to snap your stash.")
    print("Press Ctrl+C directly in this terminal to stop the script.")
    
    # Hook the global hotkey. This works even when you are actively tabbed into PoE2!
    keyboard.add_hotkey(TRIGGER_HOTKEY, capture_screen_region)
    
    # Keep the script running quietly in a loop waiting for the hotkey
    keyboard.wait()

if __name__ == "__main__":
    main()