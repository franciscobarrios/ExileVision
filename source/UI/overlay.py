import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class NameOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Windows flags for a transparent, click-through, always-on-top HUD
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.init_ui()

    def init_ui(self):
        # 1. Get a list of all physical screens connected to your system
        screens = QApplication.screens()
        print(f"Detected {len(screens)} screens.")
        
        # 2. SELECT YOUR SCREEN: 
        # Index 0 is your primary monitor. Index 1 is your secondary monitor.
        # Change this index to target the screen where your game runs!
        target_screen_index = 1 
        
        if target_screen_index < len(screens):
            screen = screens[target_screen_index]
        else:
            screen = QApplication.primaryScreen()
            
        screen_geometry = screen.geometry()
        
        # 3. Position the overlay using the specific monitor's coordinates
        # Place it near the top left of the target screen
        x = screen_geometry.x() + 100
        y = screen_geometry.y() + 100
        width = 400
        height = 150
        
        self.setGeometry(x, y, width, height)
        
        # Label layout configuration
        self.label = QLabel("ExileVision HUD Active", self)
        self.label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.label.setStyleSheet("color: #00FF00; background: transparent;")
        self.label.setGeometry(20, 20, 360, 50)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = NameOverlay()
    overlay.show()
    sys.exit(app.exec())