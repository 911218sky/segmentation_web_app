# 🩺 Vessel Measurement Tool

A vessel measurement tool powered by YOLOv13 and Streamlit for automatic detection and measurement in ultrasound images.

## 🛠️ Requirements

- Python: `>=3.11`
- CUDA: GPU acceleration support (optional)
- Docker: Recommended for deployment

## � Docker Deployment (Recommended)

### Prerequisites

- Docker with NVIDIA Container Toolkit installed
- NVIDIA GPU with CUDA support

### Quick Start

```bash
# Pull the image
docker pull ghcr.io/911218sky/segmentation_web_app:latest

# Create required directories
mkdir -p user_configs temp secrets

# Run with docker compose
docker compose up -d
```

### Manual Docker Run

```bash
docker run -d \
  --name vessel_measure \
  --gpus all \
  -p 3015:8501 \
  -v ./user_configs:/app/user_configs \
  -v ./temp:/app/temp \
  -v ./secrets:/app/secrets:ro \
  ghcr.io/911218sky/segmentation_web_app:latest
```

### Docker Scripts

```bash
# Start service (foreground)
./scripts/docker/start.sh

# Start service (background)
./scripts/docker/start.sh background

# Clean Docker resources
./scripts/docker/clean.sh

# Clean aggressively (remove all unused images)
./scripts/docker/clean.sh --aggressive
```

Access the application at: http://localhost:3015

## 💻 Local Development

### 1. Clone Repository

```bash
git clone --recursive https://github.com/911218sky/segmentation_web_app.git
cd segmentation_web_app
```

### 2. Create Virtual Environment

```bash
# Using conda (recommended)
conda create -p venv python=3.11
conda activate ./venv

# Or using venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Download Resources

Download model files and wheels from GitHub Release:

```bash
# Download from latest release
wget https://github.com/911218sky/segmentation_web_app/releases/latest/download/models.zip
wget https://github.com/911218sky/segmentation_web_app/releases/latest/download/wheels.zip

# Extract
unzip models.zip
unzip wheels.zip
```

Or manually download from [Releases](https://github.com/911218sky/segmentation_web_app/releases).

### 4. Install Dependencies

```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install YOLO requirements
pip install -r requirements_yolo.txt

# Install application dependencies
pip install -r requirements.txt

# Install YOLOv13 in development mode
cd yolov13 && pip install -e . && cd ..
```

### 5. Run Application

```bash
# Using script
./scripts/local/dev.sh

# Or directly
streamlit run app/main.py
```

Access the application at: http://localhost:8501

## 📁 Project Structure

```
scripts/
├── local/              # Local development
│   └── dev.sh          # Start local dev server
├── docker/             # Docker operations
│   ├── start.sh        # Start Docker service
│   └── clean.sh        # Clean Docker resources
├── ci/                 # CI/CD
│   └── release.sh      # Publish GitHub Release
└── internal/           # Container internal (do not run directly)
    ├── entrypoint.sh
    └── web.sh
```

## 🔧 Google Cloud Setup (Optional)

Required for Google Drive integration:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Drive API
3. Create a Service Account and download JSON key
4. Place the key file:

```bash
mkdir -p secrets
mv ~/Downloads/your-key.json secrets/service-account.json
```

## 📝 Notes

- Model files are large, ensure sufficient disk space
- GPU acceleration requires CUDA-enabled PyTorch
- Docker deployment requires NVIDIA Container Toolkit
- Default port: 8501 (local) / 3015 (Docker)
