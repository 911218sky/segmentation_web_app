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

### 3. Download Required Resources
Download the model files and wheels from the GitHub release:

```bash
# Download models.tar.gz and wheels.tar.gz from GitHub release
wget https://github.com/911218sky/segmentation_web_app/releases/download/v2/models.tar.gz
wget https://github.com/911218sky/segmentation_web_app/releases/download/v2/wheels.tar.gz

tar -xzf models.tar.gz
tar -xzf wheels.tar.gz
```

**Alternative**: Manual download
- Visit [Release v2](https://github.com/911218sky/segmentation_web_app/releases/tag/v2)
- Download `models.tar.gz` and `wheels.tar.gz`
- Place the files in the project root directory

### 4. Install Dependencies
```bash
# Install PyTorch with CUDA support (recommended)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install YOLOv12 requirements
pip install -r requirements_yolo.txt

# Install application dependencies
pip install -r requirements.txt

# Install YOLOv12 in development mode
cd ./yolov12
pip install -e .
cd ..
```

## 🚀 Usage Guide

### Launch Application
```bash
streamlit run app/main.py
```

**Important Notes**:
- Ensure all installation steps are completed before running the application
- For GPU acceleration, make sure CUDA-enabled PyTorch is properly installed
- Model files require several GB of disk space, ensure sufficient storage capacity