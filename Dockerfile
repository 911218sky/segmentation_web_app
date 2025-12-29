FROM sky1218/pytorch:2.7.1-cuda12.8-py3.11

ARG USER_ID=1000
ARG GROUP_ID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt requirements_yolo.txt ./

# 下載 wheels 並安裝 Python 套件，下載 models（自動取得最新版本）
RUN pip install --upgrade pip setuptools wheel \
    && apt-get update && apt-get install -y --no-install-recommends unzip curl \
    && curl -L -o wheels.zip https://github.com/911218sky/segmentation_web_app/releases/latest/download/wheels.zip \
    && curl -L -o models.zip https://github.com/911218sky/segmentation_web_app/releases/latest/download/models.zip \
    && unzip wheels.zip && unzip models.zip \
    && pip install -r requirements_yolo.txt \
    && pip install -r requirements.txt \
    && rm -rf wheels wheels.zip models.zip \
    && apt-get purge -y unzip curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 yolov13
COPY yolov13 ./yolov13
RUN pip install -e ./yolov13

# 建立使用者與目錄
RUN groupadd -g ${GROUP_ID} appgroup 2>/dev/null || true \
    && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash appuser 2>/dev/null || true \
    && mkdir -p user_configs temp/uploaded_videos temp/uploaded_images temp/output_videos logs \
    && chown -R ${USER_ID}:${GROUP_ID} /app

USER ${USER_ID}:${GROUP_ID}

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py"]
