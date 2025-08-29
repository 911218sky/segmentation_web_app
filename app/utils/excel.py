import pandas as pd
from io import BytesIO
from typing import List, Dict, Any
import numpy as np

from processing import IntervalStat

def generate_excel_img_results(results: List[Dict[str, Any]]) -> BytesIO:
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
                '檢測信心度': np.round(stats.get('confidence', 0), 3),
                '測量線條數量': stats.get('num_lines', 0),
                '平均長度 (mm)': np.round(stats.get('mean_length', 0), 3),
                '標準差 (mm)': np.round(stats.get('std_length', 0), 3),
                '最大長度 (mm)': np.round(stats.get('max_length', 0), 3),
                '最小長度 (mm)': np.round(stats.get('min_length', 0), 3),
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
            {'統計項目': '成功率', '數值': np.round(len(successful_results) / len(results) * 100, 1), '單位': '%'},
            {'統計項目': '平均檢測信心度', '數值': np.round(sum(all_confidences) / len(all_confidences), 3), '單位': ''},
            {'統計項目': '總測量線條數', '數值': sum(all_num_lines), '單位': '條'},
            {'統計項目': '平均線條數量', '數值': np.round(sum(all_num_lines) / len(all_num_lines), 1), '單位': '條/張'},
            {'統計項目': '整體平均長度', '數值': np.round(sum(all_mean_lengths) / len(all_mean_lengths), 3), '單位': 'mm'},
            {'統計項目': '最大平均長度', '數值': np.round(max(all_mean_lengths), 3), '單位': 'mm'},
            {'統計項目': '最小平均長度', '數值': np.round(min(all_mean_lengths), 3), '單位': 'mm'},
        ]
    else:
        summary_data = [
            {'統計項目': '總圖片數量', '數值': len(results), '單位': '張'},
            {'統計項目': '成功處理數量', '數值': 0, '單位': '張'},
            {'統計項目': '失敗處理數量', '數值': len(results), '單位': '張'},
            {'統計項目': '成功率', '數值': 0, '單位': '%'},
        ]

    # 創建 DataFrame
    main_df = pd.DataFrame(main_data)
    summary_df = pd.DataFrame(summary_data)
    
    # 創建 Excel 檔案
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 寫入主要結果
        main_df.to_excel(writer, sheet_name='詳細測量結果', index=False)
        
        # 寫入統計摘要
        summary_df.to_excel(writer, sheet_name='統計摘要', index=False)
        
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
    
    output.seek(0)
    return output

def generate_excel_video_results(results: Dict[str, IntervalStat]) -> BytesIO:
    """
    從影片區間分析結果生成 Excel 檔案
    
    Args:
        results: 字典，鍵為檔案名稱或標識，值為 IntervalStat 物件
    
    Returns:
        BytesIO: Excel 檔案的二進位數據流
    """
    # 準備主要數據
    main_data = []
    for name, stat in results.items():
        main_data.append({
            '名稱': name,
            '開始時間 (s)': np.round(stat.start_s, 3),
            '結束時間 (s)': np.round(stat.end_s, 3),
            '幀數': stat.frame_count,
            '平均尺寸 (mm)': np.round(stat.mean_of_means_mm, 3),
            '最大平均尺寸 (mm)': np.round(stat.max_of_means_mm, 3),
            '最大尺寸出現時間 (s)': np.round(stat.max_at_s, 3)
        })

    # 準備統計摘要
    total_intervals = len(main_data)
    total_frames = sum(item['幀數'] for item in main_data) if main_data else 0
    if main_data:
        mean_of_means_list = [item['平均尺寸 (mm)'] for item in main_data]
        summary_data = [
            {'統計項目': '總區間數', '數值': total_intervals, '單位': '段'},
            {'統計項目': '總幀數', '數值': total_frames, '單位': '幀'},
            {'統計項目': '平均平均尺寸', '數值': np.round(np.mean(mean_of_means_list), 3), '單位': 'mm'},
            {'統計項目': '整體最大平均尺寸', '數值': np.round(np.max(mean_of_means_list), 3), '單位': 'mm'},
            {'統計項目': '整體最大尺寸', '數值': np.round(np.max([stat.max_of_means_mm for stat in results.values()]), 3), '單位': 'mm'},
        ]
    else:
        summary_data = [
            {'統計項目': '總區間數', '數值': 0, '單位': '段'}
        ]

    # 創建 DataFrame
    main_df = pd.DataFrame(main_data)
    summary_df = pd.DataFrame(summary_data)

    # 創建 Excel 檔案
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        main_df.to_excel(writer, sheet_name='詳細統計結果', index=False)
        summary_df.to_excel(writer, sheet_name='統計摘要', index=False)

        # 格式化工作表寬度
        ws_main = writer.sheets['詳細統計結果']
        widths_main = [20, 15, 15, 10, 18, 20, 22]
        for i, width in enumerate(widths_main, start=1):
            ws_main.column_dimensions[chr(64 + i)].width = width

        ws_sum = writer.sheets['統計摘要']
        ws_sum.column_dimensions['A'].width = 20
        ws_sum.column_dimensions['B'].width = 15
        ws_sum.column_dimensions['C'].width = 10

    output.seek(0)
    return output