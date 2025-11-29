# Dockerfile
FROM sky1218/pytorch:2.7.1-cuda12.8-py3.11

# build args
ARG USER_ID=1000
ARG GROUP_ID=1000

# 非互動式與 streamlit env
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# 複製檔案（先複製 requirements 等）
COPY requirements.txt requirements_yolo.txt ./
COPY wheels ./wheels
COPY yolov13 ./yolov13
COPY scripts ./scripts

# 安裝系統依賴、Python 套件、安裝 yolov13，然後移除 build-time 套件與清理暫存
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential git curl ca-certificates ffmpeg \
      libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
      libjpeg-dev zlib1g-dev libsndfile1 libssl-dev libffi-dev pkg-config \
 && python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements_yolo.txt \
 && pip install --no-cache-dir -r requirements.txt \
 && cd yolov13 && pip install --no-cache-dir -e . && cd .. \
 # 移除 build-only 套件與清理暫存
 && apt-get purge -y --auto-remove build-essential pkg-config libssl-dev libffi-dev \
 && rm -rf /var/lib/apt/lists/* /root/.cache/pip /app/wheels

# 建群組與使用者，建立目錄並把 /app 全部 chown 給該 user
RUN groupadd -g ${GROUP_ID} appgroup 2>/dev/null || true \
 && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash appuser 2>/dev/null || true \
 && mkdir -p /app/user_configs /app/logs \
 && chown -R ${USER_ID}:${GROUP_ID} /app \
 && chmod +x /app/scripts/start-all.sh 2>/dev/null || true

# 以非 root user 執行（runtime 也可用 docker-compose 的 user: 覆蓋）
USER ${USER_ID}:${GROUP_ID}

EXPOSE 8501

CMD ["bash", "scripts/start-all.sh"]