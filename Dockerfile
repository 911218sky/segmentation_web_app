FROM python:3.11.13-slim

# 非互動式安裝；提升可觀察性
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

COPY requirements.txt requirements_yolo.txt ./
COPY wheels ./wheels
COPY yolov12 ./yolov12
COPY scripts ./scripts

# Install system deps, python deps, install yolov12, then purge build-time deps & caches
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential git curl ca-certificates ffmpeg \
      libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
      libjpeg-dev zlib1g-dev libsndfile1 libssl-dev libffi-dev pkg-config \
    && python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 \
    && pip install --no-cache-dir -r requirements_yolo.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && cd yolov12 && pip install --no-cache-dir -e . && cd .. \
    && apt-get purge -y --auto-remove build-essential pkg-config libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip /app/wheels


# 建議建立非 root 使用者（安全性）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 暴露 streamlit port
EXPOSE 8501

# 預設啟動命令
CMD ["bash", "scripts/start-all.sh"]