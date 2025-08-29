# Dockerfile
FROM python:3.11.13-slim

# 非互動式安裝；提升可觀察性
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 這兩個 ARG 會由 docker-compose 傳入（預設 1000）
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG USERNAME=appuser
ARG GROUPNAME=appuser

WORKDIR /app

# 先複製需要的檔案
COPY requirements.txt requirements_yolo.txt ./ 
COPY wheels ./wheels
COPY yolov12 ./yolov12
COPY scripts ./scripts
COPY app ./app

# 安裝系統依賴、Python 套件、安裝 yolov12，然後移除 build-time 套件與清理暫存
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

# 建立 group 和 user，使用傳入的 UID/GID（若群組已存在就忽略）
RUN groupadd -g ${GROUP_ID} ${GROUPNAME} 2>/dev/null || true \
 && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash ${USERNAME} 2>/dev/null || true \
 # 確保 /app 權限給 appuser
 && chown -R ${USER_ID}:${GROUP_ID} /app

# 建議建立非 root 使用者（安全性）
USER ${USERNAME}

# 暴露 streamlit port
EXPOSE 8501

# 預設啟動命令（假設你已有 scripts/start-all.sh）
CMD ["bash", "scripts/start-all.sh"]