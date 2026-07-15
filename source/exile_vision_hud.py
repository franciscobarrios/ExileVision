import sys
import cv2
import numpy as np
import easyocr
import requests
import keyboard
from PIL import ImageGrab
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Global configurations
LEAGUE = "Runes of Aldur"
##TEMPLATE_PATH = "exalted_template.png"
TEMPLATE_PATH = "divine_template.png"

# This class handles heavy OCR & Image Matching in a background thread
# so the transparent GUI window never becomes unresponsive.
class AnalysisThread(QThread):
    value_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("Initializing local OCR engine...")
        self.reader = easyocr.Reader(['en'], gpu=False)

    def fetch_live_prices(self):
        """
        Fetches live POE2 currency prices using the correct poe.ninja POE2 api endpoint.
        """
        # Note the '/poe2/api' prefix for Path of Exile 2
        url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={LEAGUE}&type=Currency"
        
        prices = {
            "Divine Orb": 7.4,       # Realistic fallback for PoE2
            "Exalted Orb": 0.017     # Fallback (1/424th of a divine ~ 0.017 chaos)
        }
        
        try:
            res = requests.get(url, headers={'User-Agent': 'ExileVision/1.0'}, timeout=5)
            if res.status_code == 200:
                lines = res.json().get('lines', [])
                for line in lines:
                    name = line.get('currencyTypeName')
                    if name in prices:
                        prices[name] = line.get('chaosEquivalent', prices[name])
                        print(f"Fetched live price: {name} = {prices[name]} Chaos")
        except Exception as e:
            print(f"Error fetching live prices from poe.ninja: {e}")
            
        return prices

    def count_orbs(self, img_rgb, img_gray, template_path):
        """
        Matches a template image on screen and runs OCR on stack numbers.
        """
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            return 0
            
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.85)
        
        total_orbs = 0
        processed_points = []
        
        for pt in zip(*loc[::-1]):
            if any(abs(pt[0] - p[0]) < 10 and abs(pt[1] - p[1]) < 10 for p in processed_points):
                continue
            processed_points.append(pt)
            
            # Crop slightly above/right of template boundary to isolate stack size text
            crop_y1, crop_y2 = max(0, pt[1] - 25), pt[1] + 20
            crop_x1, crop_x2 = max(0, pt[0] - 5), pt[0] + w + 5
            
            roi = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]
            ocr_res = self.reader.readtext(roi, allowlist='0123456789')
            
            stack = 1
            if ocr_res:
                try:
                    stack = int(ocr_res[0][1])
                except ValueError:
                    stack = 1
            total_orbs += stack
            
        return total_orbs

    def run(self):
        self.value_updated.emit("Scanning...")
        try:
            # 1. Grab fresh system screen capture
            screenshot = ImageGrab.grab(all_screens=True)
            img_rgb = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            
            # 2. Get live PoE2 market rates
            rates = self.fetch_live_prices()
            
            # 3. Find and count both currencies
            # (Make sure you have both "divine_template.png" and "exalted_template.png" in your folder!)
            divines_count = self.count_orbs(img_rgb, img_gray, "divine_template.png")
            exalted_count = self.count_orbs(img_rgb, img_gray, "exalted_template.png")
            
            # 4. Calculate total combined worth in Chaos
            total_value_chaos = (divines_count * rates["Divine Orb"]) + (exalted_count * rates["Exalted Orb"])
            
            print(f"Analysis complete: Found {divines_count} Divines and {exalted_count} Exalteds.")
            
            # 5. Display the result
            self.value_updated.emit(f"Net Worth: {total_value_chaos:.1f} c")
            
        except Exception as e:
            print(f"Error during scan: {e}")
            self.value_updated.emit("Scan Failed")
    value_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("Initializing local OCR engine...")
        # Initialize EasyOCR (set gpu=True if you have an NVIDIA card set up)
        self.reader = easyocr.Reader(['en'], gpu=False)

    def fetch_live_price(self):
        url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={LEAGUE}&type=Currency"
        try:
            res = requests.get(url, headers={'User-Agent': 'ExileVision/1.0'}, timeout=5)
            if res.status_code == 200:
                lines = res.json().get('lines', [])
                for line in lines:
                    if line.get('currencyTypeName') == 'Divine Orb':
                        return line.get('chaosEquivalent', 0.0)
        except Exception as e:
            print(f"Error fetching price: {e}")
        return 120.0  # Fallback manual rate if API is offline

    def run(self):
        self.value_updated.emit("Scanning...")
        try:
            # Capture all display screens
            screenshot = ImageGrab.grab(all_screens=True)
            img_rgb = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            
            template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.value_updated.emit("Missing Template File!")
                return
                
            w, h = template.shape[::-1]
            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.85)
            
            total_divines = 0
            processed_points = []
            
            for pt in zip(*loc[::-1]):
                # Remove duplicate positive matches within close proximity
                if any(abs(pt[0] - p[0]) < 10 and abs(pt[1] - p[1]) < 10 for p in processed_points):
                    continue
                processed_points.append(pt)
                
                # Crop a bounding box slightly above and to the right to catch stack numbers
                crop_y1, crop_y2 = max(0, pt[1] - 25), pt[1] + 20
                crop_x1, crop_x2 = max(0, pt[0] - 5), pt[0] + w + 5
                
                roi = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]
                ocr_res = self.reader.readtext(roi, allowlist='0123456789')
                
                stack = 1
                if ocr_res:
                    try:
                        stack = int(ocr_res[0][1])
                    except ValueError:
                        stack = 1
                total_divines += stack

            rate = self.fetch_live_price()
            total_value = total_divines * rate
            
            # Send the result string back to the main GUI thread safely
            self.value_updated.emit(f"Net Worth: {total_value:.1f} c")
        except Exception as e:
            print(f"Error during scan: {e}")
            self.value_updated.emit("Scan Failed")


class ExileVisionOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Configure window flags for transparent desktop overlays
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Multi-monitor position handler
        screens = QApplication.screens()
        # Uses your secondary monitor (index 1) if available, otherwise falls back to index 0
        screen = screens[1] if len(screens) > 1 else QApplication.primaryScreen()
        geo = screen.geometry()
        
        # Position 50 pixels offset from top-left of target screen
        self.setGeometry(geo.x() + 50, geo.y() + 50, 450, 100)
        
        # UI Elements
        self.label = QLabel("ExileVision: Ready (Ctrl+Alt+S)", self)
        self.label.setFont(QFont("Impact", 24))
        self.label.setStyleSheet("color: #FFB300; background: transparent; font-weight: bold;")
        self.label.setGeometry(10, 10, 430, 80)
        
        # Setup worker thread
        self.analysis_thread = AnalysisThread()
        self.analysis_thread.value_updated.connect(self.update_display_text)
        
        # Register global hotkeys
        keyboard.add_hotkey("ctrl+alt+s", self.trigger_scan)
        keyboard.add_hotkey("ctrl+shift+q", self.exit_application)
        
    def trigger_scan(self):
        if not self.analysis_thread.isRunning():
            self.analysis_thread.start()
            
    def update_display_text(self, text):
        self.label.setText(text)

    def exit_application(self):
        print("Exiting ExileVision... Goodbye!")
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = ExileVisionOverlay()
    overlay.show()
    sys.exit(app.exec())