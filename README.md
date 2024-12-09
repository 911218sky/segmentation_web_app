# 🩺 Vascular Measurement Tool v0.1

This is a vascular measurement tool based on **UNet3Plus** and **Streamlit**, designed for automatic identification and measurement of vascular lengths in images. It is suitable for medical imaging analysis scenarios.

---

## Features

- 🖼️ **Multi-image Support**: Upload and process multiple images simultaneously.
- 🔍 **Vascular Measurement**: Automatically identify vessels and measure their lengths with adjustable parameters.
- 🎨 **Visualization**: Mark vessels on processed images and display measured lengths.
- 📥 **Batch Download**: Pack processed results into a ZIP file for convenient download.

---

## Installation Guide

### 1️⃣ System Requirements
- Python version: `>=3.8`

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Ensure Model File
Place the pre-trained model file `best_model.pth` in the `models/` directory.

---

## Usage Instructions

### Launch the Application
Run the following command in the project directory:
```bash
streamlit run ./app/main.py
```

### Steps

1. **Upload Images**: Supports JPG and PNG formats, and allows uploading multiple images simultaneously.
2. **Set Measurement Parameters**:
   - Number of vertical lines
   - Line width
   - Minimum/maximum line length
   - Vessel depth
   - Line color
3. **Start Processing**: Click the "Start Processing" button to measure the vessels.
4. **View Results and Download**: Review processed images and download all results in a ZIP file.