import sys
import ctypes
import pygetwindow as gw
import mss
import numpy as np
import cv2
import torch
import re
from PIL import Image
from transformers import AutoProcessor, Florence2ForConditionalGeneration

# =====================================================================
# MONKEY PATCH: Fixes the Python 3.14 'forced_bos_token_id' config bug 
# in the latest transformers library before loading the model.
# =====================================================================
import transformers
if not hasattr(transformers.PretrainedConfig, "forced_bos_token_id"):
    transformers.PretrainedConfig.forced_bos_token_id = None
# =====================================================================

# 1. Force Windows to use true physical coordinates (DPI-Awareness)
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# 2. Setup the Local AI Model (Runs on GPU if available, else CPU)
print("[*] Initializing local AI engine...")
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Update model ID and load without trust_remote_code
model_id = "florence-community/Florence-2-base"

model = Florence2ForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch_dtype
).to(device)

processor = AutoProcessor.from_pretrained(model_id)
print(f"[+] Local AI running on: {device.upper()}")


def capture_poe2_window():
    """Captures the active Path of Exile 2 window using MSS."""
    all_windows = gw.getWindowsWithTitle("Path of Exile 2")
    
    # Filter out code editors or folders containing the title name
    windows = []
    for w in all_windows:
        title_lower = w.title.lower()
        if "visual studio" in title_lower or "vs code" in title_lower or ".py" in title_lower:
            continue
        if w.title.strip() == "":
            continue
        windows.append(w)

    if not windows:
        print("[-] Path of Exile 2 window not found.")
        return None
    
    window = windows[0]
    print(f"[+] Targeted window: '{window.title}'")

    if window.isMinimized:
        window.restore()
    try:
        window.activate()
    except Exception:
        pass

    # CRITICAL: Multi-monitor setup support. 
    # Removed left = max(0, left) and top = max(0, top) because secondary monitors can have negative bounds.
    left, top, width, height = window.left, window.top, window.width, window.height

    with mss.mss() as sct:
        monitor = {"top": top, "left": left, "width": width, "height": height}
        try:
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"[-] Capture failed: {e}")
            return None


def read_amount_from_crop(cropped_image_np):
    """Uses Florence-2 to read the currency amount inside a cropped slot."""
    # Convert OpenCV image (BGR) to PIL image (RGB) for the AI model
    image_rgb = cv2.cvtColor(cropped_image_np, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    
    prompt = "<OCR>"
    inputs = processor(text=prompt, images=pil_image, return_tensors="pt").to(device, torch_dtype)
    
    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=100,
        num_beams=3
    )
    
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    # Isolate only the digits from the model's textual description
    numbers = re.findall(r'\d+', generated_text)
    if numbers:
        return int(numbers[0])
    return 0


# --- Example Execution Run ---
if __name__ == "__main__":
    import time
    print("[*] Switch to your Path of Exile 2 game window. Capturing in 3 seconds...")
    time.sleep(3)
    
    # Step 1: Capture the frame
    frame = capture_poe2_window()
    
    if frame is not None:
        # Save the full screenshot
        cv2.imwrite("full_capture.png", frame)
        print("[+] Screen captured successfully!")

        # Step 2: Dynamic STASH Crop (Targeting Left Panel)
        h, w, _ = frame.shape
        print(f"[+] Calculating coordinates based on window size: {w}x{h}")

        # Stash area bounding percentages relative to the game window
        left_pct   = 0.010  # Stash grid starts near the left edge (1% width)
        right_pct  = 0.315  # Stash grid ends at roughly 31.5% width
        top_pct    = 0.130  # Currency area starts at 13% height (just below tabs)
        bottom_pct = 0.755  # Currency area ends at roughly 75.5% height

        # Convert percentages to actual pixel integers
        x1 = int(w * left_pct)
        x2 = int(w * right_pct)
        y1 = int(h * top_pct)
        y2 = int(h * bottom_pct)

        print(f"[*] Dynamic stash crop bounds: X ({x1} to {x2}), Y ({y1} to {y2})")

        # Crop the image using slicing
        test_crop = frame[y1:y2, x1:x2]
        
        cv2.imwrite("temp_test_crop.png", test_crop)
        print("[+] Saved dynamic crop of your STASH grid to 'temp_test_crop.png'.")

        # Step 3: Run local AI OCR on the crop
        detected_amount = read_amount_from_crop(test_crop)
        print(f"\n[+] Detected Text/Digits in crop: {detected_amount}")
    else:
        print("[-] Capture failed.")