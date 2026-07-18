import sys
import cv2
import numpy as np
import easyocr
import requests
import keyboard
from PIL import ImageGrab
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# Global configurations
LEAGUE = "Runes of Aldur"

class AnalysisThread(QThread):
    value_updated = pyqtSignal(dict) # Sends structured data back to the UI

    def __init__(self):
        super().__init__()
        print("Initializing local OCR engine...")
        self.reader = easyocr.Reader(['en'], gpu=False)

    def fetch_live_prices(self):
        url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={LEAGUE}&type=Currency"
        prices = {"Divine Orb": 7.4, "Exalted Orb": 0.0174} # Base PoE2 fallbacks
        
        try:
            res = requests.get(url, headers={'User-Agent': 'ExileVision/1.0'}, timeout=5)
            if res.status_code == 200:
                lines = res.json().get('lines', [])
                for line in lines:
                    name = line.get('currencyTypeName')
                    if name == "Divine Orb":
                        prices["Divine Orb"] = line.get('chaosEquivalent', prices["Divine Orb"])
                
                # Anchor Exalted Orbs mathematically to the Divine price (1 Divine = 424 Exalted)
                prices["Exalted Orb"] = prices["Divine Orb"] / 424.0
        except Exception as e:
            print(f"Error fetching live prices: {e}")
            
        return prices

    def count_orbs(self, img_gray, img_rgb, template_path):
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
        self.value_updated.emit({"status": "Scanning..."})
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            img_rgb = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            
            rates = self.fetch_live_prices()
            divines = self.count_orbs(img_gray, img_rgb, "divine_template.png")
            exalteds = self.count_orbs(img_gray, img_rgb, "exalted_template.png")
            
            total_chaos = (divines * rates["Divine Orb"]) + (exalteds * rates["Exalted Orb"])
            
            self.value_updated.emit({
                "status": "Ready",
                "divines": divines,
                "exalteds": exalteds,
                "total": f"{total_chaos:.1f} c"
            })
        except Exception as e:
            print(f"Error: {e}")
            self.value_updated.emit({"status": "Scan Failed"})


class ExileVisionOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Frameless, transparent widget flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Center/Position on Secondary Monitor if available
        screens = QApplication.screens()
        screen = screens[1] if len(screens) > 1 else QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo.x() + 60, geo.y() + 60, 380, 200)
        
        # Outer Layout & Styling Container Box
        self.main_container = QWidget(self)
        self.main_container.setObjectName("Container")
        self.main_container.setGeometry(10, 10, 360, 180)
        
        # Beautiful Cyberpunk Dark UI Theme
        self.main_container.setStyleSheet("""
            QWidget#Container {
                background-color: rgba(20, 20, 25, 230);
                border: 2px solid #3a3a4a;
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e6;
                background: transparent;
            }
            QPushButton {
                background-color: #2a2a3a;
                color: #FFB300;
                border: 1px solid #FFB300;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', Arial;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFB300;
                color: #141419;
            }
            QPushButton#ExitBtn {
                color: #ff5555;
                border: 1px solid #ff5555;
            }
            QPushButton#ExitBtn:hover {
                background-color: #ff5555;
                color: #141419;
            }
        """)
        
        # Add Drop Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.main_container.setGraphicsEffect(shadow)
        
        # UI Layout Construction
        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header / Status Indicator
        self.status_label = QLabel("ExileVision Hub • Ready", self)
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #888899;")
        layout.addWidget(self.status_label)
        
        # Net Worth Big Display
        self.net_worth_label = QLabel("0.0 c", self)
        self.net_worth_label.setFont(QFont("Impact", 36))
        self.net_worth_label.setStyleSheet("color: #FFB300;")
        layout.addWidget(self.net_worth_label)
        
        # Inventory Breakdown Subtitle
        self.breakdown_label = QLabel("Divines: 0  |  Exalted: 0", self)
        self.breakdown_label.setFont(QFont("Segoe UI", 10))
        self.breakdown_label.setStyleSheet("color: #b0b0bb;")
        layout.addWidget(self.breakdown_label)
        
        layout.addSpacing(10)
        
        # Control Buttons Row Layout
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Scan Inventory (Ctrl+Alt+S)", self)
        self.scan_btn.clicked.connect(self.trigger_scan)
        
        self.exit_btn = QPushButton("Exit", self)
        self.exit_btn.setObjectName("ExitBtn")
        self.exit_btn.clicked.connect(self.exit_application)
        
        btn_layout.addWidget(self.scan_btn, stretch=3)
        btn_layout.addWidget(self.exit_btn, stretch=1)
        layout.addLayout(btn_layout)
        
        # Background Worker Thread setup
        self.analysis_thread = AnalysisThread()
        self.analysis_thread.value_updated.connect(self.handle_ui_update)
        
        # Native Input Shortcuts
        keyboard.add_hotkey("ctrl+alt+s", self.trigger_scan)
        keyboard.add_hotkey("ctrl+shift+q", self.exit_application)
        
    def trigger_scan(self):
        if not self.analysis_thread.isRunning():
            self.scan_btn.setText("Processing...")
            self.scan_btn.setEnabled(False)
            self.analysis_thread.start()
            
    def handle_ui_update(self, data):
        if "total" in data:
            self.net_worth_label.setText(data["total"])
            self.breakdown_label.setText(f"Divines: {data['divines']}  |  Exalted: {data['exalteds']}")
            self.status_label.setText(f"ExileVision Hub • {data['status']}")
            self.scan_btn.setText("Scan Inventory (Ctrl+Alt+S)")
            self.scan_btn.setEnabled(True)
        else:
            self.status_label.setText(f"ExileVision Hub • {data['status']}")
            
    def exit_application(self):
        print("Safely stopping application background listeners...")
        QApplication.quit()

    # Window window-dragging helpers so user can reposition the UI anywhere on screen!
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = ExileVisionOverlay()
    overlay.show()
    sys.exit(app.exec())