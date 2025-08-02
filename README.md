# 🩺 Vessel Measurement Tool v0.2

A cutting-edge vessel measurement tool powered by YOLOv12 and Streamlit, designed for advanced medical image analysis to automatically detect and measure vessel dimensions in ultrasound images with superior accuracy and real-time performance.

## 🛠️ System Requirements

- Python Version: `>=3.11`
- CUDA (Optional): Support for GPU acceleration

## 📦 Installation

### 1. Clone the Project
```bash
git clone --recursive https://github.com/911218sky/segmentation_web_app.git
cd segmentation_web_app
```

### 2. Create Virtual Environment (Recommended)
```bash
conda create -p venv python=3.11
conda activate ./venv
```

### 3. Install Dependencies
```bash
# Install PyTorch with CUDA support (recommended)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install YOLOv12 requirements
pip install flash_attn-2.8.2+cu12torch2.7cxx11abiFALSE-cp311-cp311-linux_x86_64.whl
pip install -r requirements_yolo.txt

# Install application dependencies
pip install -r requirements.txt

# Install YOLOv12 in development mode
cd ./yolov12
pip install -e .
```

### 4. Prepare Model File
```bash
tar -xzf models.tar.gz
```

## 🚀 Usage Guide

### Launch Application
```bash
streamlit run app/main.py
```