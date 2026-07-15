# ExileVision 👁️

An automated, non-intrusive computer vision and live overlay suite designed for **Path of Exile 2**. 

ExileVision captures your multi-monitor active layout workspace via a hotkey macro pipeline, isolates target pixel textures using OpenCV template patterns, reads item numerical stacks natively using a local OCR engine, and pushes real-time valuation calculations directly onto an always-on-top, borderless PyQt6 desktop HUD widget layout using the live `poe.ninja` market economy API layers.

## ✨ Key Features
- **Multi-Monitor Canvas Capture:** Seamless desktop scanning configurations mapping across multi-screen setups simultaneously.
- **Pixel-Matching Pattern Isolation:** Advanced OpenCV threshold template analysis targeting specific clean item assets.
- **Local OCR Extraction:** Secure, high-accuracy text extraction analyzing numeric stack sizes locally.
- **Transparent Desktop HUD:** Hardware-prioritized, borderless PyQt6 desktop display widget passing mouse events cleanly underneath.
- **Live Pricing Pipeline:** Integrates live `poe.ninja` API exchange values matching active game economy layers.

## 🛠️ Tech Stack & Requirements
- **Language:** Python 3.10+
- **Core Engineering Libraries:**
  - `opencv-python` (Image matrix analysis)
  - `easyocr` (Machine learning text extraction engine)
  - `PyQt6` (Hardware-composited GUI overlay engine)
  - `keyboard` (System-wide input macro hooks)
  - `Pillow` (Universal system screen layout frame snapshot captures)
  - `requests` (API ingestion protocols)

## 🚀 Installation & Launch Setup

1. **Clone the project environment workspace:**
   ```bash
   git clone [https://github.com/franciscobarrios/ExileVision.git](https://github.com/franciscobarrios/ExileVision.git)
   cd ExileVision