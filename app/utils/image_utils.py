import cv2
import numpy as np
from typing import List, Tuple
from pathlib import Path
import tempfile
import shutil
from PIL import Image

def convert_pil_to_temp_files(images: List[Tuple[str, Image.Image]]) -> Tuple[List[Path], callable]:
    """將PIL圖片轉換為臨時文件"""
    temp_files = []
    
    # 創建臨時目錄
    temp_dir_path = Path(tempfile.mkdtemp(prefix="convert_pil_to_temp_files_"))
    
    for i, (filename, image) in enumerate(images):
        try:
            # 將 PIL 圖片轉換為 OpenCV 格式
            if isinstance(image, Image.Image):
                image_array = np.array(image)
                if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                    image_cv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                else:
                    image_cv = image_array
            else:
                image_cv = image
            
            # 創建臨時檔案
            temp_file_path = temp_dir_path / f"{filename}_{i:04d}.jpg"
            cv2.imwrite(str(temp_file_path), image_cv)
            temp_files.append(temp_file_path)
            
        except Exception as e:
            print(f"轉換 {filename} 時發生錯誤: {str(e)}")
            continue
    
    def cleanup():
        """清理所有臨時文件和目錄"""
        if temp_files:
            temp_dir = temp_dir_path
            try:
                shutil.rmtree(temp_dir)
                print(f"✓ 已清理臨時目錄: {temp_dir}")
            except Exception as e:
                print(f"✗ 清理臨時目錄失敗: {str(e)}")
    
    return temp_files, cleanup

def batch_resize_images_to_temp(
    image_files: List[Path], 
    target_size: Tuple[int, int] = (1024, 1024),
    prefix: str = "resized_"
) -> Tuple[List[Path], List[dict]]:
    """
    批量將圖片統一大小並保存為臨時文件
    
    Args:
        image_files: 原始圖片文件路徑列表
        target_size: 目標大小 (width, height)
        temp_dir: 臨時文件目錄，如果為None則使用系統臨時目錄
        prefix: 臨時文件名前綴
    
    Returns:
        temp_files: 臨時文件路徑列表
        image_info: 每張圖片的處理信息列表 (包含scale, padding等)
    """
    # 創建臨時目錄
    temp_dir_path = Path(tempfile.mkdtemp(prefix="batch_resize_"))
    
    temp_files = []
    image_info = []
    
    print(f"開始批量處理 {len(image_files)} 張圖片...")
    print(f"臨時目錄: {temp_dir_path}")
    
    for i, image_file in enumerate(image_files):
        try:
            # 載入原始圖片
            original_image = cv2.imread(str(image_file))
            
            if original_image is None:
                print(f"警告: 無法載入圖片 {image_file}")
                continue
            
            # 調整圖片大小
            resized_image, scale, padding = resize_image_uniform(original_image, target_size)
            
            # 生成臨時文件名
            temp_filename = f"{prefix}{image_file.stem}_{i:04d}.jpg"
            temp_file_path = temp_dir_path / temp_filename
            
            # 保存調整大小後的圖片
            success = cv2.imwrite(str(temp_file_path), resized_image)
            
            if success:
                temp_files.append(temp_file_path)
                
                # 記錄處理信息
                info = {
                    'original_path': image_file,
                    'temp_path': temp_file_path,
                    'original_shape': original_image.shape,
                    'resized_shape': resized_image.shape,
                    'scale': scale,
                    'padding': padding,
                    'target_size': target_size
                }
                image_info.append(info)
            else:
                print(f"✗ 保存失敗: {image_file.name}")
                
        except Exception as e:
            print(f"✗ 處理 {image_file.name} 時發生錯誤: {str(e)}")
            continue
    
    return temp_files, image_info

def batch_resize_with_cleanup(
    image_files: List[Path], 
    target_size: Tuple[int, int] = (1024, 1024)
) -> Tuple[List[Path], List[dict], callable]:
    """
    批量處理圖片並提供清理函數
    
    Args:
        image_files: 原始圖片文件路徑列表
        target_size: 目標大小 (width, height)
    
    Returns:
        temp_files: 臨時文件路徑列表
        image_info: 處理信息列表
        cleanup_func: 清理臨時文件的函數
    """    
    temp_files, image_info = batch_resize_images_to_temp(image_files, target_size)
    
    def cleanup():
        """清理所有臨時文件和目錄"""
        if temp_files:
            temp_dir = temp_files[0].parent
            try:
                shutil.rmtree(temp_dir)
                print(f"✓ 已清理臨時目錄: {temp_dir}")
            except Exception as e:
                print(f"✗ 清理臨時目錄失敗: {str(e)}")
    
    return temp_files, image_info, cleanup

def resize_image_uniform(image: np.ndarray, target_size: Tuple[int, int] = (1024, 1024)) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    將圖片統一調整到指定大小，保持長寬比並添加黑邊
    
    Args:
        image: 原始圖片
        target_size: 目標大小 (width, height)
    
    Returns:
        resized_image: 調整大小後的圖片
        scale: 縮放比例
        padding: 填充邊距 (left, top)
    """
    h, w = image.shape[:2]
    target_w, target_h = target_size
    
    # 計算縮放比例，選擇較小的比例以保持完整圖片
    scale = min(target_w / w, target_h / h)
    
    # 計算新尺寸
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # 調整圖片大小
    resized_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 計算填充邊距
    pad_top = (target_h - new_h) // 2
    pad_bottom = target_h - new_h - pad_top
    pad_left = (target_w - new_w) // 2
    pad_right = target_w - new_w - pad_left
    
    # 添加黑邊
    padded_image = cv2.copyMakeBorder(
        resized_img, 
        pad_top, pad_bottom, pad_left, pad_right,
        cv2.BORDER_CONSTANT, 
        value=[0, 0, 0]
    )
    
    return padded_image, scale, (pad_left, pad_top)