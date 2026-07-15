import sys
import cv2
import numpy as np
import easyocr
import requests
import os
import keyboard
from PIL import ImageGrab
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

LEAGUE = "Runes of Aldur"
TEMPLATE_PATH = "divine_template.png"

# We run the heavy OCR and Image Matching on a separate thread 
# so your overlay window never freezes up while analyzing the screen!
class AnalysisThread(QThread):
    value_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("Initializing local OCR engine...")
        self.reader = easyocr.Reader(['en'], gpu=False)

    def fetch_live_price(self):
        url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={LEAGUE}&type=Currency"
        try:
            res = requests.get(url, headers={'User-Agent': 'ExileVision/1.0'})
            if res.status_code == 200:
                lines = res.json().get('lines', [])
                for line in lines:
                    if line.get('currencyTypeName') == 'Divine Orb':
                        return line.get('chaosEquivalent', 0.0)
        except Exception:
            pass
        return 120.0

    def run(self):
        self.value_updated.emit("Scanning...")
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            img_rgb = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            
            template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_GRAYSCALE)
            if template is None:
                self.value_updated.emit("Missing Template!")
                return
                
            w, h = template.shape[::-1]
            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.85)
            
            total_divines = 0
            processed_points = []
            
            for pt in zip(*loc[::-1]):
                if any(abs(pt[0] - p[0]) < 10 and abs(pt[1] - p[1]) < 10 for p in processed_points):
                    continue
                processed_points.append(pt)
                
                crop_y1, crop_y2 = max(0, pt[1] - 25), pt[1] + 20
                crop_x1, crop_x2 = max(0, pt[0] - 5), pt[0] + w + 5
                
                roi = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]
                ocr_res = self.reader.readtext(roi, allowlist='0123456789')
                
                stack = 1
                if ocr_res:
                    try: stack = int(ocr_res[0][1])
                    except ValueError: stack = 1
                total_divines += stack

            rate = self.fetch_live_price()
            total_value = total_divines * rate
            
            # Send the text back to the main UI overlay window safely
            self.value_updated.emit(f"Net Worth: {total_value:.1f} c")
        except Exception as e:
            self.value_updated.emit("Scan Failed")

class ExileVisionOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Position cleanly on screen 2
        screens = QApplication.screens()
        screen = screens[1] if len(screens) > 1 else QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo.x() + 50, geo.y() + 50, 450, 100)
        
        self.label = QLabel("ExileVision: Ready (Ctrl+Alt+S)", self)
        self.label.setFont(QFont("Impact", 28))
        self.label.setStyleSheet("color: #FFB300; background: transparent; font-weight: bold;")
        self.label.setGeometry(10, 10, 430, 80)
        
        # Setup background scanning thread pipeline
        self.analysis_thread = AnalysisThread()
        self.analysis_thread.value_updated.connect(self.update_display_text)
        
        # Listen for global hotkey macro input
        keyboard.add_hotkey("ctrl+alt+s", self.trigger_scan)
        
    def trigger_scan(self):
        if not self.analysis_thread.isRunning():
            self.analysis_thread.start()
            
    def update_display_text(self, text):
        self.label.setText(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = ExileVisionOverlay()
    overlay.show()
    sys.exit(app.exec())