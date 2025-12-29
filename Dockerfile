FROM pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime

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
COPY wheels ./wheels

# 安裝 Python 套件
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements_yolo.txt \
    && pip install -r requirements.txt \
    && rm -rf wheels

# 複製並安裝 yolov13
COPY yolov13 ./yolov13
RUN pip install -e ./yolov13

# 複製應用程式
COPY app ./app
COPY scripts ./scripts
COPY models ./models
COPY .streamlit ./.streamlit

# 建立使用者與目錄
RUN groupadd -g ${GROUP_ID} appgroup 2>/dev/null || true \
    && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash appuser 2>/dev/null || true \
    && mkdir -p user_configs temp/uploaded_videos temp/uploaded_images temp/output_videos logs \
    && chown -R ${USER_ID}:${GROUP_ID} /app \
    && chmod +x scripts/*.sh

USER ${USER_ID}:${GROUP_ID}

EXPOSE 8501

CMD ["bash", "scripts/internal/entrypoint.sh"]
