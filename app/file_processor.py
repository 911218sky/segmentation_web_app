import io
import os
import tempfile
import zipfile
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from PIL import Image
import torch
import torch.nn as nn
import logging
from state_manager import ProcessingParams
from utils import infer_batch, draw_average_length, group_lengths

# 設置日誌
logger = logging.getLogger(__name__)

def process_images(
    model: nn.Module,
    uploaded_files: List[UploadedFile],
    params: ProcessingParams,
    device: torch.device,
    transform: Any
) -> List[Tuple[Image.Image, Image.Image, List[float]]]:
    """
    處理上傳的圖片並返回結果。

    Args:
        model: 用於推理的模型
        uploaded_files: 上傳的圖片文件列表
        params: 處理參數
        device: 運行設備（CPU/GPU）
        transform: 圖片轉換函數

    Returns:
        List[Tuple[Image.Image, Image.Image, List[float]]]: 處理結果列表
    """
    results = []
    try:
        # 使用臨時目錄來存儲圖片數據
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for idx, uploaded_file in enumerate(uploaded_files):
                temp_path = os.path.join(temp_dir, f"temp_{idx}.png")
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                image_paths.append(temp_path)

            # 執行批量推理
            results = infer_batch(
                image_paths=image_paths,
                model=model,
                device=device,
                fp_precision="fp16",
                num_lines=params.num_lines,
                line_width=params.line_width,
                min_length_mm=params.min_length_mm,
                max_length_mm=params.max_length_mm,
                depth_cm=params.depth_cm,
                line_color=params.line_color,
                line_length_weight=params.line_length_weight,
                deviation_threshold=params.deviation_threshold,
                transform=transform,
            )

    except Exception as e:
        logger.exception("處理圖片時發生錯誤")
        st.error(f"處理圖片時發生錯誤: {e}")
        return []

    # 在處理後的圖片上繪製平均長度標註
    for i, (img, mask, lengths) in enumerate(results):
        # 如果沒有測量到血管，則將平均長度設為0
        if len(lengths) <= 0:
            lengths = [0]
        if img is not None:
            results[i] = (
                draw_average_length(img, lengths, params.deviation_percent),
                mask,
                lengths
            )

    return results

def create_zip_archive(
    results: List[Tuple[Image.Image, Image.Image, List[float]]],
    uploaded_files: List
) -> io.BytesIO:
    """
    將處理後的圖片加入一個 ZIP 壓縮包，並返回包含該 ZIP 文件的 BytesIO 對象。

    參數:
        results: List of Tuple，其中每個元祖包含 (處理後圖片, 原圖, 其他資訊)
        uploaded_files: 源上傳文件列表，用來獲取原始檔名

    返回:
        BytesIO 對象，包含 ZIP 壓縮包的所有內容
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        filename_count = {}
        for idx, (img, _, _) in enumerate(results):
            if img:
                base_filename = os.path.basename(uploaded_files[idx].name)
                if base_filename in filename_count:
                    filename_count[base_filename] += 1
                    name, ext = os.path.splitext(base_filename)
                    filename = f"{name}_{filename_count[base_filename]}{ext}"
                else:
                    filename_count[base_filename] = 0
                    filename = base_filename

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG", quality=75, optimize=True)
                img_byte_arr.seek(0)
                zip_file.writestr(f"processed_{filename}", img_byte_arr.read())
    zip_buffer.seek(0)
    return zip_buffer

def create_excel_report(measurement_data: List[Dict[str, str]]) -> Optional[io.BytesIO]:
    """
    創建測量結果的Excel報告。
    """
    try:
        # 創建DataFrame
        df = pd.DataFrame(measurement_data)
        
        # 將DataFrame轉換為Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='測量結果', index=False)
            worksheet = writer.sheets['測量結果']
            
            # 設置列寬
            worksheet.set_column('A:A', 30)  # 檔名列寬
            worksheet.set_column('B:B', 15)  # 平均長度列寬

        excel_buffer.seek(0)
        return excel_buffer
    except Exception as e:
        logger.exception("創建Excel報告時發生錯誤")
        st.error(f"創建Excel報告時發生錯誤: {e}")
        return None

def collect_measurement_data(
    results: List[Tuple[Image.Image, Image.Image, List[float]]],
    uploaded_files: List[UploadedFile],
    selected_measurements: Dict[str, float]
) -> List[Dict[str, str]]:
    """
    收集測量數據用於報告生成。
    
    參數:
        results: 處理結果列表
        uploaded_files: 上傳的文件列表
        selected_measurements: 已選擇的測量值字典，鍵為測量鍵，值為選中的測量值
    """
    measurement_data: List[Dict[str, str]] = []
    valid_measurements = []
    
    for idx, (processed_img, _, _) in enumerate(results):
        filename = os.path.basename(uploaded_files[idx].name)
        measurement_key = f"measurement_{filename}_{idx}"
        if measurement_key in selected_measurements:
            selected_measurement = selected_measurements[measurement_key]
            measurement_data.append({
                "檔名": filename,
                "平均長度 (mm)": float(f"{selected_measurement:.2f}")
            })
            valid_measurements.append(selected_measurement)
        else:
            status = "未測量到血管" if processed_img else "處理失敗"
            measurement_data.append({
                "檔名": filename,
                "平均長度 (mm)": status
            })
            
    if len(valid_measurements) > 0:
        grouped_lengths = group_lengths(valid_measurements)
        if grouped_lengths:
            # 將所有分組的長度組合成文字
            avg_length_text = " or ".join([f"{length:.2f}" for length in grouped_lengths])
            measurement_data.insert(0, {
                "檔名": "全部平均",
                "平均長度 (mm)": avg_length_text
            })
    return measurement_data 