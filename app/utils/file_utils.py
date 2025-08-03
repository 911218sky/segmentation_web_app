from pathlib import Path
from typing import List

def get_image_files(source_dir: Path, formats: List[str]) -> List[Path]:
    """
    獲取指定目錄下的所有圖片文件
    
    Args:
        source_dir: 圖片目錄路徑
        formats: 支援的文件格式列表
    
    Returns:
        圖片文件路徑列表
    """
    image_files = []
    for ext in formats:
        image_files.extend(source_dir.glob(ext))
    return sorted(image_files)  # 排序確保一致性

def ensure_output_dir(output_dir: Path) -> None:
    """
    確保輸出目錄存在
    
    Args:
        output_dir: 輸出目錄路徑
    """
    output_dir.mkdir(parents=True, exist_ok=True)