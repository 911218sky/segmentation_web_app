# 🩺 Vessel Measurement Tool v0.2

A vessel measurement tool based on **UNet3Plus** and **Streamlit**, designed for medical image analysis to automatically identify and measure vessel lengths in ultrasound images.

[中文](README_zh.md) | English

## ✨ Features

- 🖼️ **Multi-image Processing**: Support simultaneous upload and processing of multiple images
- 🔍 **Smart Measurement**: Automatic vessel identification and precise measurement
- 🎨 **Visualization**: Clear marking of vessel locations and measurement results
- 📊 **Data Analysis**: Generate detailed Excel measurement reports
- 🌐 **Multi-language**: Support for English and Traditional Chinese interfaces
- 💾 **Parameter Management**: Save and load commonly used measurement settings

## 🛠️ System Requirements

- Python Version: `>=3.8`
- CUDA (Optional): Support for GPU acceleration
- OS: Windows / Linux / macOS

## 📦 Installation

### 1. Clone the Project
```bash
git clone https://github.com/yourusername/vessel-measurement-tool.git
cd vessel-measurement-tool
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Prepare Model File
Place the pre-trained model `model_traced_v3.pt` in the `models/` directory.

## 🚀 Usage Guide

### Launch Application
```bash
streamlit run app/main.py
```

### Operation Flow

1. **Upload Images**
   - Supports JPG, PNG formats
   - Multiple image upload
   - Drag and drop support

2. **Adjust Parameters**
   - Number of vertical lines: Control measurement precision
   - Line width: Adjust marker visibility
   - Min/Max line length: Filter outliers
   - Vessel depth: Calibrate measurements
   - Deviation threshold: Control measurement accuracy
   - Grouping deviation: Auto-group similar measurements
   - Line color: Customize marker color

3. **Review Results**
   - Real-time preview of processed images
   - Select best measurements
   - Confirm measurement results

4. **Download Results**
   - Download processed images (ZIP format)
   - Export measurement report (Excel format)

## ⚙️ Configuration

Adjust the following settings in `config.py`:

```python
model:
    model_dir: str    # Model directory path
    filename: str     # Model filename

image:
    size: tuple      # Input image size
    channels: int    # Image channels
```

## 📁 Project Structure

```
vessel-measurement-tool/
├── app/
│   ├── i18n/               # Internationalization
│   │   ├── translations.py # Translation files
│   │   └── language_manager.py
│   ├── main.py            # Main program
│   ├── utils.py           # Utility functions
│   ├── file_processor.py  # File processing
│   └── state_manager.py   # State management
├── models/                # Model files
├── config.py             # Configuration
└── requirements.txt      # Dependencies
```

## ❓ Troubleshooting

1. **Model File Not Found**
   - Verify correct model filename
   - Check if model is in correct directory

2. **Memory Issues**
   - Reduce number of concurrent images
   - Close memory-intensive applications

3. **Slow Processing**
   - Check GPU acceleration status
   - Adjust image size or batch size

## 🤝 Contributing

Issues and Pull Requests are welcome to improve the project.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 📮 Contact

- Author: [Your Name]
- Email: [your.email@example.com]
- GitHub: [Your GitHub Profile]

## 📝 Changelog

### v0.2 (2024-03)
- ✨ Added multi-language support
- 🔧 Optimized measurement algorithm
- 📊 Added Excel report feature

### v0.1 (2024-02)
- 🎉 Initial release
- 🔍 Basic measurement functionality
- 📦 Batch processing support