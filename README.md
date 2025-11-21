# 🩺 Vessel Measurement Tool v0.2
A cutting-edge vessel measurement tool powered by YOLOv12 and Streamlit, designed for advanced medical image analysis to automatically detect and measure vessel dimensions in ultrasound images with superior accuracy and real-time performance.

## 🛠️ System Requirements
- Python Version: `>=3.11`
- CUDA (Optional): Support for GPU acceleration

## 🔧 Google Cloud Service Account Setup

### Prerequisites
Before setting up the service, ensure you have:
- A Google Cloud Console account

### Step-by-Step Configuration

#### 1. Access Google Cloud Console
- Log in to [Google Cloud Console](https://console.cloud.google.com/)
- Select an existing project or create a new one for your operations

#### 2. Enable Required APIs
If your application needs to access specific APIs (e.g., Google Drive API):
- Navigate to **APIs & Services → Library**
- Search for and enable the required APIs (e.g., "Drive API")
- Click **Enable** for each required API

#### 3. Create Service Account
- Go to **IAM & Admin → Service Accounts**
- Click **+ Create Service Account**
- Enter a descriptive **name** and **description** for the service account
- Click **Create and Continue**

#### 4. Assign Permissions
- **(Recommended)** Follow the principle of least privilege
- Assign only the minimum necessary permissions for your application
- You can specify roles during creation or adjust them later in the IAM section
- Click **Continue** then **Done**

#### 5. Generate Service Account Key
- Click on the newly created service account from the list
- Navigate to the **Keys** tab
- Click **Add Key → Create new key**
- Select **JSON** format
- Click **Create**

**Important**: The browser will automatically download a `.json` file. This is the **only opportunity** to download the private key - Google only provides the original private key at creation time.

#### 6. Secure the Key File
After downloading the JSON key file:

1. **Create the secrets directory** in your project root:
   ```bash
   mkdir -p secrets
   ```

2. **Rename and move the downloaded JSON file**:
   ```bash
   # Replace 'your-project-name-xxxxx.json' with your actual downloaded filename
   mv ~/Downloads/your-project-name-xxxxx.json secrets/service-account.json
   ```

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

# Install YOLOv13 in development mode
cd ./yolov13
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
- Verify that `secrets/service-account.json` is properly configured if using Google Cloud services
- For GPU acceleration, make sure CUDA-enabled PyTorch is properly installed
- Model files require several GB of disk space, ensure sufficient storage capacity
