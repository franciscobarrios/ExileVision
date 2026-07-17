import sys
import os
import cv2
import numpy as np
import easyocr
import requests
import keyboard
from PIL import ImageGrab
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QComboBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# Global configurations
LEAGUE = "Runes of Aldur"

# Comprehensive PoE2 Currency Registry
# Adjusted to look inside your new "templates/" folder
CURRENCY_REGISTRY = {
    "Chaos Orb": {"file": "template_currencies/chaos.png", "base_value": 1.0},
    "Greater Chaos Orb": {"file": "template_currencies/greater_chaos.png", "base_value": 2.5},
    "Perfect Chaos Orb": {"file": "template_currencies/perfect_chaos.png", "base_value": 8.0},
    
    "Divine Orb": {"file": "template_currencies/divine.png", "base_value": 7.4},
    
    "Exalted Orb": {"file": "template_currencies/exalted.png", "base_value": 0.0174},  # Math: Divine / 424
    "Greater Exalted Orb": {"file": "template_currencies/greater_exalted.png", "base_value": 0.25},
    "Perfect Exalted Orb": {"file": "template_currencies/perfect_exalted.png", "base_value": 2.0},
    
    "Regal Orb": {"file": "template_currencies/regal.png", "base_value": 0.5},
    "Greater Regal Orb": {"file": "template_currencies/greater_regal.png", "base_value": 1.5},
    "Perfect Regal Orb": {"file": "template_currencies/perfect_regal.png", "base_value": 5.0},
    
    "Orb of Annulment": {"file": "template_currencies/annulment.png", "base_value": 4.0},
    "Fracturing Orb": {"file": "template_currencies/fracturing.png", "base_value": 150.0},
    "Mirror of Kalandra": {"file": "template_currencies/mirror.png", "base_value": 12000.0},
    "Hinekora's Lock": {"file": "template_currencies/hinekora.png", "base_value": 4000.0}
}

class AnalysisThread(QThread):
    value_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        print("Initializing local OCR engine...")
        # Added verbose=False to silence the default GPU warning message
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Make sure our debug folder exists
        if not os.path.exists("debug_crops"):
            os.makedirs("debug_crops")

    def fetch_live_prices(self):
        url = f"https://poe.ninja/poe2/api/economy/exchange/current/overview?league={LEAGUE}&type=Currency"
        rates = {name: data["base_value"] for name, data in CURRENCY_REGISTRY.items()}
        
        try:
            res = requests.get(url, headers={'User-Agent': 'ExileVision/1.0'}, timeout=5)
            if res.status_code == 200:
                lines = res.json().get('lines', [])
                for line in lines:
                    name = line.get('currencyTypeName')
                    if name in rates:
                        rates[name] = line.get('chaosEquivalent', rates[name])
                
                # Dynamic adjustment for Exalted baseline adjustments
                rates["Exalted Orb"] = rates["Divine Orb"] / 424.0
        except Exception as e:
            print(f"Error fetching live prices: {e}")
            
        return rates

    def count_orbs(self, img_gray, img_rgb, template_path, currency_name):
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            # Silent fail if template doesn't exist yet so script doesn't crash
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
            
            # The crop area relative to the matched template's top-left coordinates
            crop_y1 = max(0, pt[1] - 25)
            crop_y2 = pt[1] + 15
            crop_x1 = max(0, pt[0] - 5)
            crop_x2 = pt[0] + w + 5
            
            roi = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]
            
            # Save a debug image inside 'debug_crops/' to inspect where coordinates crop
            debug_filename = f"debug_crops/debug_{currency_name.lower().replace(' ', '_')}.png"
            cv2.imwrite(debug_filename, roi)
            
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
        self.value_updated.emit({"status": "Scanning Inventory..."})
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            img_rgb = np.array(screenshot)
            img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
            
            rates = self.fetch_live_prices()
            counts = {}
            total_chaos = 0.0
            
            # Loop dynamically through currency registry passing name to the counter
            for name, data in CURRENCY_REGISTRY.items():
                count = self.count_orbs(img_gray, img_rgb, data["file"], name)
                counts[name] = count
                total_chaos += count * rates[name]
            
            self.value_updated.emit({
                "status": "Ready",
                "counts": counts,
                "total_chaos": total_chaos
            })
        except Exception as e:
            print(f"Error during bulk processing: {e}")
            self.value_updated.emit({"status": "Scan Failed"})


class ExileVisionOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        screens = QApplication.screens()
        screen = screens[1] if len(screens) > 1 else QApplication.primaryScreen()
        geo = screen.geometry()
        self.setGeometry(geo.x() + 60, geo.y() + 60, 420, 240)
        
        self.main_container = QWidget(self)
        self.main_container.setObjectName("Container")
        self.main_container.setGeometry(10, 10, 400, 220)
        
        self.main_container.setStyleSheet("""
            QWidget#Container {
                background-color: rgba(20, 20, 25, 235);
                border: 2px solid #3a3a4a;
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e6;
                background: transparent;
            }
            QComboBox {
                background-color: #2a2a3a;
                color: #e0e0e6;
                border: 1px solid #4a4a5a;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Segoe UI';
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #191922;
                color: #e0e0e6;
                selection-background-color: #FFB300;
                selection-color: #141419;
            }
            QPushButton {
                background-color: #2a2a3a;
                color: #FFB300;
                border: 1px solid #FFB300;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #FFB300;
                color: #141419;
            }
            QPushButton#ExitBtn { color: #ff5555; border: 1px solid #ff5555; }
            QPushButton#ExitBtn:hover { background-color: #ff5555; color: #141419; }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.main_container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header Row Layout
        header_layout = QHBoxLayout()
        self.status_label = QLabel("ExileVision Hub • Ready", self)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #888899;")
        
        self.view_selector = QComboBox(self)
        self.view_selector.addItems(["Grand Net Worth", "Chaos Items", "Exalted Items", "Regal Items", "High Tiers"])
        self.view_selector.currentIndexChanged.connect(self.refresh_display_calculations)
        
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.view_selector)
        layout.addLayout(header_layout)
        
        # Grand Valuation Large Layout
        self.net_worth_label = QLabel("0.0 c", self)
        self.net_worth_label.setFont(QFont("Impact", 36))
        self.net_worth_label.setStyleSheet("color: #FFB300;")
        layout.addWidget(self.net_worth_label)
        
        # Dynamic Text Information Field
        self.breakdown_label = QLabel("Run a scan to analyze stash contents.", self)
        self.breakdown_label.setFont(QFont("Segoe UI", 10))
        self.breakdown_label.setStyleSheet("color: #b0b0bb;")
        layout.addWidget(self.breakdown_label)
        
        layout.addSpacing(10)
        
        # User Controls Row
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("Scan Inventory (Ctrl+Alt+S)", self)
        self.scan_btn.clicked.connect(self.trigger_scan)
        
        self.exit_btn = QPushButton("Exit", self)
        self.exit_btn.setObjectName("ExitBtn")
        self.exit_btn.clicked.connect(self.exit_application)
        
        btn_layout.addWidget(self.scan_btn, stretch=3)
        btn_layout.addWidget(self.exit_btn, stretch=1)
        layout.addLayout(btn_layout)
        
        self.latest_scan_data = None
        
        self.analysis_thread = AnalysisThread()
        self.analysis_thread.value_updated.connect(self.handle_ui_update)
        
        keyboard.add_hotkey("ctrl+alt+s", self.trigger_scan)
        keyboard.add_hotkey("ctrl+shift+q", self.exit_application)
        
    def trigger_scan(self):
        if not self.analysis_thread.isRunning():
            self.scan_btn.setText("Processing...")
            self.scan_btn.setEnabled(False)
            self.analysis_thread.start()
            
    def handle_ui_update(self, data):
        if "total_chaos" in data:
            self.latest_scan_data = data
            self.scan_btn.setText("Scan Inventory (Ctrl+Alt+S)")
            self.scan_btn.setEnabled(True)
            self.status_label.setText(f"ExileVision Hub • {data['status']}")
            self.refresh_display_calculations()
        else:
            self.status_label.setText(f"ExileVision Hub • {data['status']}")
            
    def refresh_display_calculations(self):
        if not self.latest_scan_data:
            return
            
        view_mode = self.view_selector.currentText()
        counts = self.latest_scan_data["counts"]
        
        if view_mode == "Grand Net Worth":
            self.net_worth_label.setText(f"{self.latest_scan_data['total_chaos']:.1f} c")
            self.breakdown_label.setText(f"Divines: {counts['Divine Orb']} | Chaos Stack: {counts['Chaos Orb']} | Mirrors: {counts['Mirror of Kalandra']}")
            
        elif view_mode == "Chaos Items":
            self.net_worth_label.setText(f"{counts['Chaos Orb'] + counts['Greater Chaos Orb'] + counts['Perfect Chaos Orb']} Orbs")
            self.breakdown_label.setText(f"Chaos: {counts['Chaos Orb']}  •  Greater: {counts['Greater Chaos Orb']}  •  Perfect: {counts['Perfect Chaos Orb']}")
            
        elif view_mode == "Exalted Items":
            self.net_worth_label.setText(f"{counts['Exalted Orb'] + counts['Greater Exalted Orb'] + counts['Perfect Exalted Orb']} Orbs")
            self.breakdown_label.setText(f"Exalted: {counts['Exalted Orb']}  •  Greater: {counts['Greater Exalted Orb']}  •  Perfect: {counts['Perfect Exalted Orb']}")
            
        elif view_mode == "Regal Items":
            self.net_worth_label.setText(f"{counts['Regal Orb'] + counts['Greater Regal Orb'] + counts['Perfect Regal Orb']} Orbs")
            self.breakdown_label.setText(f"Regal: {counts['Regal Orb']}  •  Greater: {counts['Greater Regal Orb']}  •  Perfect: {counts['Perfect Regal Orb']}")
            
        elif view_mode == "High Tiers":
            self.net_worth_label.setText(f"{counts['Divine Orb']} Div / {counts['Mirror of Kalandra']} Mir")
            self.breakdown_label.setText(f"Annul: {counts['Orb of Annulment']}  |  Fracture: {counts['Fracturing Orb']}  |  Lock: {counts['Hinekora\'s Lock']}")

    def exit_application(self):
        QApplication.quit()

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