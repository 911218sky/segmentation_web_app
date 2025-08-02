import streamlit as st
import numpy as np
from pathlib import Path
import zipfile
from io import BytesIO
from PIL import Image
import sys
import math

# 添加模組路徑
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# 導入自定義模組和配置
from yolo_predictor import YOLOPredictor
from config import *
from utils import process_batch_images
from excel_utils import generate_excel_from_results, generate_csv_from_results

# 頁面配置
st.set_page_config(
    page_title="血管分割與測量系統",
    page_icon="🔬",
    layout="wide"
)

# 初始化 session state
if 'predictor' not in st.session_state:
    st.session_state.predictor = None
if 'processed_results' not in st.session_state:
    st.session_state.processed_results = []

@st.cache_resource
def load_model(weights_path):
    """載入並快取 YOLO 模型"""
    try:
        if not Path(weights_path).exists():
            st.error(f"模型檔案不存在: {weights_path}")
            return None
        
        predictor = YOLOPredictor(Path(weights_path))
        return predictor
    except Exception as e:
        st.error(f"模型載入失敗: {str(e)}")
        return None

def main():
    st.title("🔬 血管分割與測量系統")
    st.markdown("---")
    
    # 自動載入本地模型
    if st.session_state.predictor is None:
        with st.spinner("正在載入本地模型..."):
            st.session_state.predictor = load_model(WEIGHTS_PATH)
    
    # 側邊欄配置
    with st.sidebar:
        st.header("⚙️ 系統配置")
        
        # 模型狀態顯示
        st.subheader("模型狀態")
        if st.session_state.predictor is not None:
            st.success(f"✅ 模型已載入")
            st.info(f"📁 模型路徑: {WEIGHTS_PATH}")
        else:
            st.error("❌ 模型載入失敗")
            st.info(f"請確認模型檔案存在於: {WEIGHTS_PATH}")
        
        # 基本處理參數
        st.subheader("基本參數")
        pixel_size_mm = st.number_input(
            "像素大小 (mm/pixel)", 
            min_value=0.01, 
            max_value=1.0, 
            value=PROCESSING_CONFIG['pixel_size_mm'], 
            step=0.01,
            help="一個像素對應的實際距離"
        )
        
        confidence_threshold = st.slider(
            "信心度閾值", 
            min_value=0.1, 
            max_value=1.0, 
            value=YOLO_CONFIG['conf'], 
            step=0.05,
            help="YOLO 檢測的信心度閾值"
        )
        
        # 線條提取參數
        st.subheader("🔍 線條提取參數")
        sample_interval = st.number_input(
            "採樣間隔 (像素)",
            min_value=1,
            max_value=100,
            value=LINE_EXTRACTION_CONFIG['sample_interval'],
            step=1,
            help="x軸採樣步距，數值越小線條越密集"
        )
        
        gradient_search_top = st.number_input(
            "往上搜尋距離 (像素)",
            min_value=1,
            max_value=50,
            value=LINE_EXTRACTION_CONFIG['gradient_search_top'],
            step=1,
            help="向上搜尋血管邊界的最大像素距離"
        )
        
        gradient_search_bottom = st.number_input(
            "往下搜尋距離 (像素)",
            min_value=1,
            max_value=50,
            value=LINE_EXTRACTION_CONFIG['gradient_search_bottom'],
            step=1,
            help="向下搜尋血管邊界的最大像素距離"
        )
        
        keep_ratio = st.slider(
            "保留寬度比例",
            min_value=0.1,
            max_value=1.0,
            value=LINE_EXTRACTION_CONFIG['keep_ratio'],
            step=0.1,
            help="用於邊界調整的寬度保留比例"
        )
        
        # 視覺化參數
        st.subheader("🎨 視覺化參數")
        line_thickness = st.number_input(
            "線條粗細",
            min_value=1,
            max_value=10,
            value=VISUALIZATION_CONFIG['line_thickness'],
            step=1,
            help="繪製線條的粗細程度"
        )
        
        line_alpha = st.slider(
            "線條透明度",
            min_value=0.1,
            max_value=1.0,
            value=VISUALIZATION_CONFIG['line_alpha'],
            step=0.1,
            help="線條的透明度，1為完全不透明"
        )
        
        # 線條顏色選擇
        line_color_option = st.selectbox(
            "線條顏色",
            options=["綠色", "紅色", "藍色", "白色", "黃色"],
            index=0,
            help="選擇線條的顏色"
        )
        
        color_map = {
            "綠色": (0, 255, 0),
            "紅色": (0, 0, 255),
            "藍色": (255, 0, 0),
            "白色": (255, 255, 255),
            "黃色": (0, 255, 255)
        }
        line_color = color_map[line_color_option]
        
        st.subheader("批次處理")
        st.info(f"📦 批次大小: {BATCH_SIZE} 張圖片")
        st.info("🚀 系統會自動進行批次推理以提高效率")
    
    # 主要內容區域
    if st.session_state.predictor is None:
        st.error("⚠️ 模型未載入，無法進行分析")
        st.info("📝 請檢查模型檔案路徑是否正確")
        return
    
    # 圖片上傳區域
    st.subheader("📤 圖片上傳")
    uploaded_files = st.file_uploader(
        "選擇血管圖片",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help=f"支援多張圖片同時上傳，系統會以 {BATCH_SIZE} 張為單位進行批次處理"
    )
    
    if uploaded_files:
        st.success(f"已上傳 {len(uploaded_files)} 張圖片")
        
        # 處理選項
        col1, col2 = st.columns(2)
        with col1:
            process_all = st.button("🚀 批次處理全部圖片", type="primary")
        with col2:
            clear_results = st.button("🗑️ 清除結果")
        
        if clear_results:
            st.session_state.processed_results = []
            st.rerun()
        
        # 批次處理圖片
        if process_all:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 準備配置參數
            line_config = {
                'sample_interval': sample_interval,
                'gradient_search_top': gradient_search_top,
                'gradient_search_bottom': gradient_search_bottom,
                'keep_ratio': keep_ratio
            }
            
            vis_config = {
                'line_color': line_color,
                'line_thickness': line_thickness,
                'line_alpha': line_alpha,
            }
            
            # 準備圖片資料
            images_data = [(f.name, Image.open(f)) for f in uploaded_files]
            total_batches = math.ceil(len(images_data) / BATCH_SIZE)
            
            status_text.text(f"開始批次處理 {len(images_data)} 張圖片 ({total_batches} 個批次)")
            
            # 批次處理
            st.session_state.processed_results = process_batch_images(
                st.session_state.predictor,
                images_data,
                pixel_size_mm,
                confidence_threshold,
                line_config,
                vis_config
            )
            
            progress_bar.progress(1.0)
            status_text.text("✅ 批次處理完成！")
        
        # 顯示結果
        if st.session_state.processed_results:
            st.subheader("📊 分析結果")
            
            # 統計摘要
            successful_results = [r for r in st.session_state.processed_results if r['success']]
            failed_results = [r for r in st.session_state.processed_results if not r['success']]
            
            if successful_results:
                col1, col2, col3, col4 = st.columns(4)
                
                all_mean_lengths = [r['stats']['mean_length'] for r in successful_results]
                
                with col1:
                    st.metric(
                        "成功處理", 
                        f"{len(successful_results)}/{len(st.session_state.processed_results)}"
                    )
                with col2:
                    st.metric("平均長度 (mm)", f"{np.mean(all_mean_lengths):.2f}")
                with col3:
                    st.metric("最大平均長度", f"{np.max(all_mean_lengths):.2f}")
                with col4:
                    st.metric("最小平均長度", f"{np.min(all_mean_lengths):.2f}")
            
            if failed_results:
                st.warning(f"⚠️ {len(failed_results)} 張圖片處理失敗")
            
            # 計算需要多少行
            successful_with_images = [r for r in successful_results if r['result'] is not None]
            
            if successful_with_images:
                # 每行顯示2張圖片
                cols_per_row = 2
                num_rows = math.ceil(len(successful_with_images) / cols_per_row)
                
                for row in range(num_rows):
                    cols = st.columns(cols_per_row)
                    
                    for col_idx in range(cols_per_row):
                        result_idx = row * cols_per_row + col_idx
                        
                        if result_idx < len(successful_with_images):
                            result = successful_with_images[result_idx]
                            
                            with cols[col_idx]:
                                st.subheader(f"📷 {result['filename']}")
                                
                                # 只顯示處理後的圖片
                                st.image(result['result'], use_container_width=True)
                                
                                # 顯示統計資料
                                stats = result['stats']
                                
                                # 使用更緊凑的佈局顯示統計數據
                                st.markdown("**📈 測量數據**")
                                
                                metrics_col1, metrics_col2 = st.columns(2)
                                with metrics_col1:
                                    st.metric("信心度", f"{stats['confidence']:.3f}")
                                    st.metric("測量線數量", stats['num_lines'])
                                with metrics_col2:
                                    st.metric("平均長度", f"{stats['mean_length']:.2f} mm")
                                    st.metric("標準差", f"{stats['std_length']:.2f} mm")
                                
                                # 顯示範圍
                                st.markdown(f"**範圍:** {stats['min_length']:.2f} - {stats['max_length']:.2f} mm")
                                
                                st.markdown("---")
            
            # 失敗結果單獨顯示
            if failed_results:
                st.subheader("❌ 處理失敗的圖片")
                for result in failed_results:
                    st.error(f"**{result['filename']}**: {result['stats'].get('error', '未知錯誤')}")
            
            # 下載結果
            if successful_results:
                st.subheader("💾 下載結果")
                
                # 準備配置參數用於 Excel 報告
                config_params_for_excel = {
                    'pixel_size_mm': pixel_size_mm,
                    'confidence_threshold': confidence_threshold,
                    'sample_interval': sample_interval,
                    'gradient_search_top': gradient_search_top,
                    'gradient_search_bottom': gradient_search_bottom,
                    'keep_ratio': keep_ratio,
                    'line_color_option': line_color_option,
                    'line_thickness': line_thickness,
                    'line_alpha': line_alpha
                }
                
                # 生成 Excel 和 CSV 檔案
                excel_buffer = None
                csv_content = None
                
                try:                    
                    excel_buffer = generate_excel_from_results(
                        st.session_state.processed_results, 
                        config_params_for_excel
                    )
                    
                    csv_content = generate_csv_from_results(st.session_state.processed_results)
                    
                except ImportError:
                    st.error("❌ 無法載入 Excel 工具，請確認 excel_utils.py 檔案存在")
                except Exception as e:
                    st.error(f"❌ Excel/CSV 生成失敗: {str(e)}")
                
                # 創建 ZIP 檔案
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    # 儲存圖片結果
                    for result in successful_results:
                        if result['result']:
                            img_buffer = BytesIO()
                            result['result'].save(img_buffer, format='JPEG')
                            zip_file.writestr(
                                f"results/result_{result['filename']}", 
                                img_buffer.getvalue()
                            )
                    
                    # 創建詳細配置報告
                    config_report = [
                        "血管分割與測量系統 - 配置與分析報告",
                        "=" * 60,
                        "",
                        "處理配置參數:",
                        f"  - 像素大小: {pixel_size_mm} mm/pixel",
                        f"  - 信心度閾值: {confidence_threshold}",
                        f"  - 批次大小: {BATCH_SIZE}",
                        "",
                        "線條提取配置:",
                        f"  - 採樣間隔: {sample_interval} 像素",
                        f"  - 往上搜尋距離: {gradient_search_top} 像素",
                        f"  - 往下搜尋距離: {gradient_search_bottom} 像素",
                        f"  - 保留寬度比例: {keep_ratio}",
                        "",
                        "視覺化配置:",
                        f"  - 線條顏色: {line_color_option}",
                        f"  - 線條粗細: {line_thickness}",
                        f"  - 線條透明度: {line_alpha}",
                        "",
                        "處理結果:",
                        f"  - 總圖片數量: {len(st.session_state.processed_results)}",
                        f"  - 成功處理: {len(successful_results)}",
                        f"  - 失敗數量: {len(failed_results)}",
                        "",
                        "詳細結果:",
                        "-" * 60,
                    ]
                    
                    for result in successful_results:
                        stats = result['stats']
                        config_report.extend([
                            f"檔案: {result['filename']}",
                            f"  信心度: {stats['confidence']:.3f}",
                            f"  測量線數量: {stats['num_lines']}",
                            f"  平均長度: {stats['mean_length']:.2f} mm",
                            f"  標準差: {stats['std_length']:.2f} mm",
                            f"  範圍: {stats['min_length']:.2f} - {stats['max_length']:.2f} mm",
                            ""
                        ])
                    
                    zip_file.writestr("configuration_and_analysis_report.txt", "\n".join(config_report))
                    
                    # 將 Excel 檔案也加入 ZIP
                    if excel_buffer:
                        zip_file.writestr("measurement_results.xlsx", excel_buffer.getvalue())
                    
                    # 將 CSV 檔案也加入 ZIP
                    if csv_content:
                        zip_file.writestr("measurement_results.csv", csv_content.encode('utf-8-sig'))
                
                # 下載按鈕佈局
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        label="📥 下載完整結果包 (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="vessel_complete_analysis_results.zip",
                        mime="application/zip",
                        help="包含圖片結果、Excel報表、CSV檔案和文字報告"
                    )
                
                with col2:
                    if excel_buffer:
                        st.download_button(
                            label="📊 下載 Excel 報表",
                            data=excel_buffer.getvalue(),
                            file_name="vessel_measurement_results.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="包含詳細測量數據、統計摘要和配置參數"
                        )
                    else:
                        st.error("Excel 生成失敗")
                
                with col3:
                    if csv_content:
                        st.download_button(
                            label="📋 下載 CSV 檔案",
                            data=csv_content,
                            file_name="vessel_measurement_results.csv",
                            mime="text/csv",
                            help="測量結果的 CSV 格式檔案"
                        )
                    else:
                        st.error("CSV 生成失敗")
                
                # 處理效率顯示
                st.metric("📊 處理效率", f"{len(successful_results)} 張成功")

if __name__ == "__main__":
    main()