import pandas as pd
from io import BytesIO
from typing import List, Dict, Any

def generate_excel_from_results(results: List[Dict[str, Any]], 
                               config_params: Dict[str, Any] = None) -> BytesIO:
    """
    從分析結果生成 Excel 檔案
    
    Args:
        results: 分析結果列表
        config_params: 配置參數字典
    
    Returns:
        BytesIO: Excel 檔案的二進位數據流
    """
    # 準備主要數據
    main_data = []
    for r in results:
        if r['success'] and 'stats' in r:
            stats = r['stats']
            main_data.append({
                '檔案名稱': r['filename'],
                '檢測信心度': round(stats.get('confidence', 0), 4),
                '測量線條數量': stats.get('num_lines', 0),
                '平均長度 (mm)': round(stats.get('mean_length', 0), 3),
                '標準差 (mm)': round(stats.get('std_length', 0), 3),
                '最大長度 (mm)': round(stats.get('max_length', 0), 3),
                '最小長度 (mm)': round(stats.get('min_length', 0), 3),
                '處理狀態': '成功'
            })
        else:
            # 失敗的結果也記錄
            error_msg = r.get('stats', {}).get('error', '未知錯誤')
            main_data.append({
                '檔案名稱': r['filename'],
                '檢測信心度': 'N/A',
                '測量線條數量': 'N/A',
                '平均長度 (mm)': 'N/A',
                '標準差 (mm)': 'N/A',
                '最大長度 (mm)': 'N/A',
                '最小長度 (mm)': 'N/A',
                '處理狀態': f'失敗: {error_msg}'
            })
    
    # 準備統計摘要數據
    successful_results = [r for r in results if r['success']]
    if successful_results:
        all_mean_lengths = [r['stats']['mean_length'] for r in successful_results]
        all_num_lines = [r['stats']['num_lines'] for r in successful_results]
        all_confidences = [r['stats']['confidence'] for r in successful_results]
        
        summary_data = [
            {'統計項目': '總圖片數量', '數值': len(results), '單位': '張'},
            {'統計項目': '成功處理數量', '數值': len(successful_results), '單位': '張'},
            {'統計項目': '失敗處理數量', '數值': len(results) - len(successful_results), '單位': '張'},
            {'統計項目': '成功率', '數值': round(len(successful_results) / len(results) * 100, 1), '單位': '%'},
            {'統計項目': '平均檢測信心度', '數值': round(sum(all_confidences) / len(all_confidences), 4), '單位': ''},
            {'統計項目': '總測量線條數', '數值': sum(all_num_lines), '單位': '條'},
            {'統計項目': '平均線條數量', '數值': round(sum(all_num_lines) / len(all_num_lines), 1), '單位': '條/張'},
            {'統計項目': '整體平均長度', '數值': round(sum(all_mean_lengths) / len(all_mean_lengths), 3), '單位': 'mm'},
            {'統計項目': '最大平均長度', '數值': round(max(all_mean_lengths), 3), '單位': 'mm'},
            {'統計項目': '最小平均長度', '數值': round(min(all_mean_lengths), 3), '單位': 'mm'},
        ]
    else:
        summary_data = [
            {'統計項目': '總圖片數量', '數值': len(results), '單位': '張'},
            {'統計項目': '成功處理數量', '數值': 0, '單位': '張'},
            {'統計項目': '失敗處理數量', '數值': len(results), '單位': '張'},
            {'統計項目': '成功率', '數值': 0, '單位': '%'},
        ]
    
    # 準備配置參數數據
    config_data = []
    if config_params:
        config_data = [
            {'參數類別': '基本參數', '參數名稱': '像素大小', '數值': config_params.get('pixel_size_mm', 'N/A'), '單位': 'mm/pixel'},
            {'參數類別': '基本參數', '參數名稱': '信心度閾值', '數值': config_params.get('confidence_threshold', 'N/A'), '單位': ''},
            {'參數類別': '線條提取', '參數名稱': '採樣間隔', '數值': config_params.get('sample_interval', 'N/A'), '單位': '像素'},
            {'參數類別': '線條提取', '參數名稱': '往上搜尋距離', '數值': config_params.get('gradient_search_top', 'N/A'), '單位': '像素'},
            {'參數類別': '線條提取', '參數名稱': '往下搜尋距離', '數值': config_params.get('gradient_search_bottom', 'N/A'), '單位': '像素'},
            {'參數類別': '線條提取', '參數名稱': '保留寬度比例', '數值': config_params.get('keep_ratio', 'N/A'), '單位': ''},
            {'參數類別': '視覺化', '參數名稱': '線條顏色', '數值': config_params.get('line_color_option', 'N/A'), '單位': ''},
            {'參數類別': '視覺化', '參數名稱': '線條粗細', '數值': config_params.get('line_thickness', 'N/A'), '單位': ''},
            {'參數類別': '視覺化', '參數名稱': '線條透明度', '數值': config_params.get('line_alpha', 'N/A'), '單位': ''},
        ]
    
    # 創建 DataFrame
    main_df = pd.DataFrame(main_data)
    summary_df = pd.DataFrame(summary_data)
    config_df = pd.DataFrame(config_data)
    
    # 創建 Excel 檔案
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 寫入主要結果
        main_df.to_excel(writer, sheet_name='詳細測量結果', index=False)
        
        # 寫入統計摘要
        summary_df.to_excel(writer, sheet_name='統計摘要', index=False)
        
        # 寫入配置參數
        if config_data:
            config_df.to_excel(writer, sheet_name='配置參數', index=False)
        
        # 獲取工作簿以進行格式化
        workbook = writer.book
        
        # 格式化主要結果工作表
        main_worksheet = writer.sheets['詳細測量結果']
        main_worksheet.column_dimensions['A'].width = 25  # 檔案名稱
        main_worksheet.column_dimensions['B'].width = 15  # 檢測信心度
        main_worksheet.column_dimensions['C'].width = 15  # 測量線條數量
        main_worksheet.column_dimensions['D'].width = 18  # 平均長度
        main_worksheet.column_dimensions['E'].width = 15  # 標準差
        main_worksheet.column_dimensions['F'].width = 18  # 最大長度
        main_worksheet.column_dimensions['G'].width = 18  # 最小長度
        main_worksheet.column_dimensions['H'].width = 20  # 處理狀態
        
        # 格式化統計摘要工作表
        summary_worksheet = writer.sheets['統計摘要']
        summary_worksheet.column_dimensions['A'].width = 20
        summary_worksheet.column_dimensions['B'].width = 15
        summary_worksheet.column_dimensions['C'].width = 10
        
        # 格式化配置參數工作表
        if config_data:
            config_worksheet = writer.sheets['配置參數']
            config_worksheet.column_dimensions['A'].width = 15
            config_worksheet.column_dimensions['B'].width = 20
            config_worksheet.column_dimensions['C'].width = 15
            config_worksheet.column_dimensions['D'].width = 10
    
    output.seek(0)
    return output

def generate_csv_from_results(results: List[Dict[str, Any]]) -> str:
    """
    從分析結果生成 CSV 字符串
    
    Args:
        results: 分析結果列表
    
    Returns:
        str: CSV 格式的字符串
    """
    data = []
    for r in results:
        if r['success'] and 'stats' in r:
            stats = r['stats']
            data.append({
                '檔案名稱': r['filename'],
                '檢測信心度': round(stats.get('confidence', 0), 4),
                '測量線條數量': stats.get('num_lines', 0),
                '平均長度(mm)': round(stats.get('mean_length', 0), 3),
                '標準差(mm)': round(stats.get('std_length', 0), 3),
                '最大長度(mm)': round(stats.get('max_length', 0), 3),
                '最小長度(mm)': round(stats.get('min_length', 0), 3),
                '處理狀態': '成功'
            })
        else:
            error_msg = r.get('stats', {}).get('error', '未知錯誤')
            data.append({
                '檔案名稱': r['filename'],
                '檢測信心度': 'N/A',
                '測量線條數量': 'N/A',
                '平均長度(mm)': 'N/A',
                '標準差(mm)': 'N/A',
                '最大長度(mm)': 'N/A',
                '最小長度(mm)': 'N/A',
                '處理狀態': f'失敗: {error_msg}'
            })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8-sig')