import os
import io
import zipfile
import tempfile
from typing import List, Tuple, Dict, Any
import torch
from PIL import Image
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import torchvision.transforms as T
import logging
import numpy as np

from model import UNet3Plus
from utils import draw_average_length, infer_batch

# 設置日誌配置，方便調試和監控
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設置 Streamlit 頁面配置
st.set_page_config(
    page_title="🩺 血管測量工具 v0.1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 檢查是否有可用的 GPU，若沒有則使用 CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 定義模型存放的目錄和文件名
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
MODEL_FILENAME = 'best_model.pth'
model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)

# 定義推理時的圖片轉換流程
infer_transform: T.Compose = T.Compose([
    T.Resize((256, 256)),  # 調整圖片大小為 256x256
    T.ToTensor(),          # 將圖片轉換為張量
])

@st.cache_resource(show_spinner=False)
def load_model(model_path: str) -> UNet3Plus:
    """
    加載預訓練的 UNet3Plus 模型並緩存，以避免重複加載。
    
    參數:
        model_path (str): 模型文件的路徑。
    
    返回:
        UNet3Plus: 加載好的模型實例。
    """
    try:
        logger.info(f"正在從 {model_path} 加載模型")
        model = UNet3Plus().to(device)  # 初始化模型並移動到相應設備
        checkpoint = torch.load(model_path, map_location=device)  # 加載模型檢查點
        model.load_state_dict(checkpoint)  # 加載模型參數
        model.eval()  # 設置模型為評估模式
        logger.info("模型加載成功")
        return model
    except FileNotFoundError:
        logger.error(f"模型文件未找到: {model_path}")
        st.error("❌ 模型文件未找到，請確保模型文件放在 models/ 目錄下。")
        st.stop()  # 停止應用的執行
    except Exception as e:
        logger.exception("加載模型時發生錯誤")
        st.error(f"加載模型時發生錯誤: {e}")
        st.stop()

def main():
    """
    主函數，負責設置頁面內容和用戶交互。
    """
    # 設置頁面的標題和描述
    st.title("🩺 血管測量工具")
    st.write("🔍 此工具可以自動識別並測量圖片中的血管長度。")

    # 加載模型，如果模型文件不存在，已在 load_model 中處理錯誤
    model = load_model(model_path)

    # 步驟 1：上傳圖片
    st.markdown("## 步驟 1: 上傳圖片")
    uploaded_files = st.file_uploader(
        "上傳多張圖片進行測量（支援格式：JPG, PNG）",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png"]
    )

    # 步驟 2：調整參數
    st.markdown("## 步驟 2: 設定測量參數")
    with st.expander("🔧 點擊此處設置參數", expanded=True):
        # 使用雙欄佈局提升界面整潔度
        col1, col2 = st.columns(2)
        with col1:
            num_lines = st.slider(
                "垂直線的數量",
                min_value=1,
                max_value=100,
                value=15,
                step=1,
                help="設定圖片中垂直線的數量，用於血管的測量。"
            )
            line_width = st.slider(
                "線條寬度",
                min_value=1,
                max_value=10,
                value=3,
                step=1,
                help="設定血管線條的寬度。"
            )
            min_length_mm = st.slider(
                "最小線條長度 (mm)",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                help="設定血管線條的最小長度（毫米）。"
            )
            max_length_mm = st.slider(
                "最大線條長度 (mm)",
                min_value=4.0,
                max_value=20.0,
                value=7.0,
                step=0.1,
                help="設定血管線條的最大長度（毫米）。"
            )
        with col2:
            depth_cm = st.slider(
                "深度 (cm)",
                min_value=1.0,
                max_value=20.0,
                value=3.2,
                step=0.1,
                help="設定血管深度（厘米）。"
            )
            line_length_weight = st.slider(
                "調整線條長度權重",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.05,
                help="調整線條長度在測量中的權重。"
            )
            line_color = st.radio(
                "線條顏色",
                options=[
                    ('綠色', (0, 255, 0)),
                    ('紅色', (255, 0, 0)),
                    ('藍色', (0, 0, 255)),
                    ('黃色', (255, 255, 0)),
                    ('白色', (255, 255, 255)),
                ],
                index=0,
                format_func=lambda x: x[0],
                help="選擇標記血管的線條顏色。"
            )[1]

    # 設置開始處理的按鈕
    if st.button("開始處理"):
        if not uploaded_files:
            st.warning("⚠️ 請上傳至少一張圖片。")
            return

        # 處理圖片並獲取結果
        results = process_images(
            uploaded_files,
            model,
            {
                'num_lines': num_lines,
                'line_width': line_width,
                'min_length_mm': min_length_mm,
                'max_length_mm': max_length_mm,
                'depth_cm': depth_cm,
                'line_color': line_color,
                'line_length_weight': line_length_weight
            }
        )

        # 顯示處理結果
        if results:
            display_results(results, uploaded_files)

def process_images(
    uploaded_files: List[UploadedFile],
    model: UNet3Plus,
    params: Dict[str, Any]
) -> List[Tuple[Image.Image, Image.Image, List[float]]]:
    """
    處理上傳的圖片，進行血管測量並返回結果。

    參數:
        uploaded_files (List[UploadedFile]): 用戶上傳的圖片文件列表。
        model (UNet3Plus): 加載好的模型實例。
        params (Dict[str, Any]): 測量參數設置。

    返回:
        List[Tuple[Image.Image, Image.Image, List[float]]]: 每張圖片的處理結果，包括原圖、處理後圖像和測量長度。
    """
    results = []
    try:
        # 使用臨時目錄來存儲上傳的圖片，確保處理後自動刪除
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for idx, uploaded_file in enumerate(uploaded_files):
                # 獲取文件的擴展名
                file_extension = uploaded_file.type.split('/')[-1]
                temp_filename = f"temp_{idx}.{file_extension}"
                temp_path = os.path.join(temp_dir, temp_filename)
                # 將上傳的文件寫入臨時目錄
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                image_paths.append(temp_path)

            # 顯示處理進度提示
            with st.spinner("處理圖片中，請稍候..."):
                # 執行批量推理
                results = infer_batch(
                    image_paths=image_paths,
                    model=model,
                    device=device,
                    num_lines=params['num_lines'],
                    line_width=params['line_width'],
                    min_length_mm=params['min_length_mm'],
                    max_length_mm=params['max_length_mm'],
                    depth_cm=params['depth_cm'],
                    line_color=params['line_color'],
                    line_length_weight=params['line_length_weight'],
                    transform=infer_transform
                )
                logger.info("圖片推理完成")

    except Exception as e:
        logger.exception("處理圖片時發生錯誤")
        st.error(f"處理時發生錯誤: {e}")
        
    # 在處理後的圖片上繪製平均長度標註
    for i, result in enumerate(results):
        results[i] = (draw_average_length(result[0], result[2]), result[1], result[2])

    return results

def display_results(results: List[Tuple[Image.Image, Image.Image, List[float]]], uploaded_files: List[UploadedFile]):
    """
    顯示處理後的圖片結果並提供下載功能。

    參數:
        results (List[Tuple[Image.Image, Image.Image, List[float]]]): 每張圖片的處理結果。
        uploaded_files (List[UploadedFile]): 用戶上傳的圖片文件列表。
    """
    st.markdown("## 處理結果")
    if not results:
        st.warning("沒有可顯示的處理結果。")
        return

    # 壓縮所有處理後的圖片為一個 ZIP 檔案
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for idx, (img, _, _) in enumerate(results):
            if img:
                filename = os.path.basename(uploaded_files[idx].name)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                zip_file.writestr(f"processed_{filename}", img_bytes.getvalue())

    # 使用網格布局，每行顯示兩張圖片
    cols = st.columns(2)
    for idx, (processed_img, _, measurements) in enumerate(results):
        with cols[idx % 2]:
            filename = os.path.basename(uploaded_files[idx].name)
            st.markdown(f"### {filename}")
            if processed_img:
                st.image(processed_img, caption="處理後的圖像", use_container_width=True)
                mean_length = np.mean(measurements) if len(measurements) > 0 else 0
                st.write(f"平均測量長度: {mean_length:.2f} mm")
            else:
                st.error(f"處理失敗: {filename}")

    # 提供下載所有處理後的圖片的按鈕
    if zip_buffer.getvalue():
        zip_buffer.seek(0)  # 將緩衝區指針重置到開始位置
        st.download_button(
            "📥 下載所有處理後的圖片",
            data=zip_buffer,
            file_name="processed_images.zip",
            mime="application/zip",
            key="download_button",
            help="點擊此按鈕下載所有處理後的圖片壓縮包。"
        )

if __name__ == '__main__':
    main()