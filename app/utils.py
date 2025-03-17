import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG

import logging
import math
from typing import Any, List, Optional, Tuple

import numpy as np
import numpy.typing as npt
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.transforms.functional as T
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

current_file = os.path.abspath(__file__)
file_name = os.path.basename(current_file)
logger = logging.getLogger(file_name)

def release_vram():
    """
    釋放 GPU (VRAM) 記憶體並打印釋放的記憶體和目前使用的記憶體。
    """
    # 獲取釋放前的 GPU 記憶體使用情況
    before_allocated = torch.cuda.memory_allocated()

    # 釋放 GPU 緩存記憶體
    torch.cuda.empty_cache()

    # 獲取釋放後的 GPU 記憶體使用情況
    after_allocated = torch.cuda.memory_allocated()

    # 計算釋放量
    freed_allocated = before_allocated - after_allocated

    logger.info(f"釋放了 {freed_allocated / 1024 ** 2:.2f} MB 記憶體，目前使用 {after_allocated / 1024 ** 2:.2f} MB 記憶體")

def infer_batch(
    image_paths: List[str],
    model: nn.Module,
    batch_size: int = 32,
    max_workers: int = CONFIG.threading.max_workers,
    fp_precision: str = "fp16",
    num_lines: int = 10,
    line_color: Tuple[int, int, int] = (0, 255, 0),
    line_width: int = 2,
    depth_cm: float = 3.2,
    min_length_mm: float = 1.0,
    max_length_mm: float = 7.0,
    line_length_weight: float = 1,
    deviation_threshold: float = 0.2,
    transform: Optional[transforms.Compose] = None,
    device: Optional[torch.device] = None,
    progress_callback: Optional[callable] = None,
) -> List[Tuple[Optional[Image.Image], Optional[Image.Image], List[float]]]:
    """
    批次推理多張圖片並返回處理後的圖片、僅包含線條的遮罩覆蓋圖片和線條長度列表。

    Args:
        image_paths (List[str]): 
            圖片的檔案路徑列表。必須提供有效的圖片路徑，以便函數能夠載入並處理圖片。

        model (nn.Module): 
            用於推理的預訓練模型。該模型應該是已經訓練好的分割模型實例，用於生成圖片的遮罩。

        batch_size (int, optional):
            每次在 GPU 上推理的圖片數量。預設為 32。

        max_workers (int, optional):
            最大工作執行緒數，預設為 CONFIG.threading.max_workers。

        fp_precision (str, optional): 
            模型運行時的浮點精度。可選值為 `"fp16"` 或 `"fp32"`，預設為 `"fp32"`。選擇較低的精度可以節省計算資源，但可能會影響模型的準確性。

        num_lines (int, optional): 
            要在圖片上繪製的垂直線條數量，預設為 10。該值決定了在圖片上標註的線條數量。

        line_color (Tuple[int, int, int], optional): 
            繪製線條的顏色，使用 RGB 格式表示。預設為綠色 `(0, 255, 0)`。可以根據需要調整為其他顏色。

        line_width (int, optional): 
            繪製線條的寬度，預設為 2。該值決定了線條的粗細程度。

        depth_cm (float, optional): 
            圖片所代表的實際深度，以厘米為單位，預設為 3.2。該值用於計算像素到毫米的轉換比例。

        min_length_mm (float, optional): 
            繪製線條的最小長度，以毫米為單位。只有長度大於或等於該值的線條才會被繪製。預設為 1.0。

        max_length_mm (float, optional): 
            繪製線條的最大長度，以毫米為單位。只有長度小於或等於該值的線條才會被繪製。預設為 7.0。

        line_length_weight (float, optional): 
            線條長度權重，預設為 1。該值用於調整線條長度結果的影響。
            
        deviation_threshold (float, optional): 
            允許的最大偏差比例（例如 0.2 表示 20%）。

        transform (transforms.Compose, optional): 
            圖片的預處理轉換管道。若未提供，將使用預設的轉換，包括調整大小和轉換為張量。可以自定義轉換以適應不同的預處理需求。

        device (torch.device, optional): 
            運行模型的設備，可以是 CPU 或 GPU。若未提供，將自動選擇可用的 GPU（如果有），否則使用 CPU。

        progress_callback (Optional[callable], optional):
            進度回調函數，接受三個參數：
            - stage: 當前階段 ("loading", "inference", "drawing")
            - current: 當前進度
            - total: 總進度

    Returns:
        List[Tuple[Optional[Image.Image], Optional[Image.Image], List[float], str]]: 
            返回一個列表，其中每個元素是一個包含四個元素的元組：
            1. 處理後的圖片，包含繪製的垂直線條和長度標註。如果處理失敗，為 `None`。
            2. 僅包含繪製線條的遮罩覆蓋圖片。如果處理失敗，為 `None`。
            3. 繪製的所有線條的長度列表，以毫米為單位。如果處理失敗，為空列表。
    """
    total_images = len(image_paths)
    if total_images == 0:
        return []

    # 設置設備
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 設置模型精度
    model = model.to(device)
    if fp_precision == "fp16":
        model = model.half()
    elif fp_precision == "fp32":
        model = model.float()
    elif fp_precision == "bf16":
        model = model.bfloat16()
    else:
        raise ValueError("無效的 `fp_precision` 值，請選擇 'fp16'、'fp32'、'bf16' 或 'fp8'。")

    # 設置模型為評估模式
    model.eval()

    # 定義預設轉換（保持寬高比）
    if transform is None:
        transform: T.Compose = T.Compose([
            T.Resize((256, 256)),
            T.Grayscale(num_output_channels=1), 
            T.ToTensor(),
        ])

    # 計算總批次數
    num_batches = math.ceil(total_images / batch_size)
    valid_images = [[] for _ in range(num_batches)] 
    valid_sizes = [[] for _ in range(num_batches)]
    valid_paths = [[] for _ in range(num_batches)]
    masks = []

    # 載入圖片階段
    loaded_images = 0
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_images)
        current_batch_paths = image_paths[start_idx:end_idx]

        # 載入和預處理當前批次的圖片
        for image_path in current_batch_paths:
            try:
                # 讀取並轉換圖片
                original_image = Image.open(image_path).convert("RGB")
                original_size = original_image.size
                transformed_image = transform(original_image)

                # 儲存有效的圖片資訊
                valid_images[batch_idx].append(transformed_image)
                valid_sizes[batch_idx].append(original_size)
                valid_paths[batch_idx].append(image_path)
                
                loaded_images += 1
                if progress_callback:
                    progress_callback("loading", loaded_images, total_images)
            except Exception as e:
                logger.error(f"無法載入或轉換圖片 {image_path}: {e}")

    # 推理階段
    processed_images = 0
    with torch.no_grad():
        for batch_idx in range(num_batches):
            if not valid_images[batch_idx]:  # 跳過空批次
                continue
                
            # 堆疊成批次張量
            input_tensor = torch.stack(valid_images[batch_idx]).to(device)

            # 將圖像張量的精度與模型匹配
            if fp_precision == "fp16":
                input_tensor = input_tensor.half()
            elif fp_precision == "fp32":
                input_tensor = input_tensor.float()
            
            output = model(input_tensor)
            # 將輸出轉換為0-1之間的值
            output = torch.sigmoid(output)
            # 生成遮罩
            masks.extend((output > 0.5).cpu().numpy().astype(np.uint8) * 255)
            
            processed_images += len(valid_images[batch_idx])
            if progress_callback:
                progress_callback("inference", processed_images, total_images)
    
    # 釋放 VRAM
    release_vram()
    
    # 將 valid_images、valid_sizes 和 valid_paths 展平
    valid_images = [img for batch in valid_images for img in batch]
    valid_sizes = [size for batch in valid_sizes for size in batch]
    valid_paths = [path for batch in valid_paths for path in batch]
    
    def process_image(i: int) -> Tuple[Optional[Image.Image], Optional[Image.Image], List[float]]:
        mask = masks[i]
        original_width, original_height = valid_sizes[i]
        current_image_path = valid_paths[i]

        # 將遮罩轉回 PIL Image 並縮放回原始尺寸
        mask_pil = Image.fromarray(mask.squeeze()).resize(
            (original_width, original_height), Image.NEAREST)
        mask_np_resized = np.array(mask_pil)

        # 載入原始圖片
        try:
            original_image = Image.open(current_image_path).convert("RGB")
        except Exception as e:
            logger.error(f"無法載入原始圖片 {current_image_path}: {e}")
            return (None, None, [])

        # 繪製垂直線條並標註長度
        image_with_lines, line_lengths = draw_vertical_lines_with_length_mm(
            image=original_image.copy(),
            mask_np=mask_np_resized,
            num_lines=num_lines,
            line_color=line_color,
            line_width=line_width,
            depth_cm=depth_cm,
            image_height_px=original_height,
            min_length_mm=min_length_mm,
            max_length_mm=max_length_mm,
            line_length_weight=line_length_weight,
            deviation_threshold=deviation_threshold
        )

        # 繪製遮罩
        image_with_mask = draw_mask(
            image=original_image.copy(), 
            mask_np=mask_np_resized,
            color=(*line_color, 200),
            threshold=0.5
        )

        return (image_with_lines, image_with_mask, line_lengths)
    
    results = []
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, i) for i in range(len(valid_images))]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            results.append(future.result())
            if progress_callback:
                progress_callback("drawing", i + 1, len(valid_images))

    return results

def draw_mask(image: Image.Image, mask_np: np.ndarray, color: Tuple[int, int, int, int] = (255, 0, 0, 128), threshold: float = 0.5) -> Image.Image:
    """
    將遮罩轉換為半透明顏色覆蓋在原始圖片上。

    Args:
        image (Image.Image): 
            原始圖片，RGB 格式。

        mask_np (np.ndarray):
            遮罩陣列，二值化的 numpy array。

        color (Tuple[int, int, int, int], optional): 
            遮罩的顏色及透明度，預設為半透明紅色 `(255, 0, 0, 128)`。

        threshold (float, optional): 
            遮罩的閾值，預設為 0.5。
            當遮罩值大於閾值時，將該位置的像素設為指定的顏色和透明度。

    Returns:
        Image.Image: 
            覆蓋了遮罩的原始圖片，RGB 格式。
    """
    # 將遮罩轉換為 RGBA 格式
    mask_rgba = np.zeros((*mask_np.shape, 4), dtype=np.uint8)
    # 當遮罩值大於 threshold 時，將該位置的像素設為指定的顏色和透明度
    # 例如: color=(255,0,0,128) 代表半透明的紅色
    mask_rgba[mask_np > threshold] = color

    # 將遮罩轉換為 PIL Image
    mask_image = Image.fromarray(mask_rgba, 'RGBA')

    # 將原始圖片轉換為 RGBA
    original_rgba = image.convert('RGBA')

    # 將遮罩覆蓋在原始圖片上
    result = Image.alpha_composite(original_rgba, mask_image)

    # 轉回 RGB 格式
    return result.convert('RGB')

def find_mask_at_x(mask_np: npt.NDArray[Any], target_x: int, search_range: int = 5) -> Tuple[int, int]:
    """
    在給定的 x 座標或鄰近 x 周圍搜尋該垂直方向上的遮罩範圍。
    返回找到的最上與最下的 y 座標索引，如果完全找不到，回傳 None, None。
    """
    # 從mask中擷取非零的索引
    y_indices, x_indices = np.nonzero(mask_np)
    candidate_y = y_indices[x_indices == target_x]

    if len(candidate_y) > 0:
        return candidate_y.min(), candidate_y.max()

    # 如果在這個 x 沒找到，則在鄰近 x 搜尋
    _, width = mask_np.shape
    for shift in range(1, search_range + 1):
        # 向右搜尋
        if target_x + shift < width:
            candidate_y_right = y_indices[x_indices == target_x + shift]
            if len(candidate_y_right) > 0:
                return candidate_y_right.min(), candidate_y_right.max()

        # 向左搜尋
        if target_x - shift >= 0:
            candidate_y_left = y_indices[x_indices == target_x - shift]
            if len(candidate_y_left) > 0:
                return candidate_y_left.min(), candidate_y_left.max()

    # 找不到合適的遮罩
    return None, None

def group_lengths(line_lengths: List[float], deviation_percent: float = 0.1) -> List[float]:
    """
    將線條長度分組，並依照差距百分比分組顯示。

    Args:
        line_lengths (List[float]): 線條長度列表
        deviation_percent (float): 分組的差距百分比，預設為10%

    Returns:
        List[float]: 每個分組的平均長度列表
    """
    if not line_lengths:
        return []

    # 轉換為 numpy array 並過濾 0
    lengths = np.array(line_lengths)
    lengths = lengths[lengths != 0]
    
    if len(lengths) == 0:
        return []

    # 排序
    sorted_lengths = np.sort(lengths)
    
    # 計算相鄰元素的差距百分比
    diffs = np.abs(np.diff(sorted_lengths) / sorted_lengths[:-1])
    
    # 找出差距大於閾值的位置，這些位置就是分組的邊界
    group_boundaries = np.where(diffs > deviation_percent)[0] + 1
    
    # 使用 split 根據邊界分組
    groups = np.split(sorted_lengths, group_boundaries)
    
    # 計算每組的平均值
    means = np.array([np.mean(group) for group in groups])
    
    return means.tolist()

def draw_average_length(image: Image.Image, line_lengths: List[float], deviation_percent: float = 0.1) -> Image.Image:
    """
    在圖片上繪製平均長度標註，並依照差距百分比分組顯示。

    Args:
        image (Image.Image): 
            處理後的圖片，包含繪製的垂直線條和長度標註。

        line_lengths (List[float]): 
            繪製的所有線條的長度列表，以毫米為單位。

        deviation_percent (float):
            分組的差距百分比，預設為10%。

    Returns:
        Image.Image: 
            繪製完成的圖片。
    """
    assert len(line_lengths) > 0, "線條長度列表不能為空"

    # 計算每個分組的平均長度
    if deviation_percent > 0:
        length_groups = group_lengths(line_lengths, deviation_percent)
        # 將所有分組的長度和數量組合成文字
        avg_length_text = " or ".join([
            f"{length:.2f}mm" 
            for length in length_groups
        ])
        avg_length_text = f"Average Length: {avg_length_text}"
    else:
        avg_length_text = f"Average Length: {np.mean(line_lengths):.2f}mm"
        
    # 在處理後的圖片底部繪製平均長度文字
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    # 使用 getbbox 計算文字尺寸
    bbox = draw.textbbox((0, 0), avg_length_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 計算文字位置，使其居中並位於圖片底部
    text_x = (image.width - text_width) // 2
    text_y = image.height - text_height - 20  # 圖片底部上方 20 像素

    # 繪製半透明背景矩形以增強文字對比度
    draw.rectangle(
        [
            text_x - 5,
            text_y - 5,
            text_x + text_width + 5,
            text_y + text_height + 5
        ],
        fill=(0, 0, 0, 128)
    )

    # 繪製平均長度文字
    draw.text((text_x, text_y), avg_length_text,
              fill=(255, 255, 255), font=font)

    return image

def draw_vertical_lines_with_length_mm(
    image: Image.Image,
    mask_np: npt.NDArray[np.int8],
    num_lines: int = 15,
    line_color: Tuple[int, int, int] = (0, 255, 0),
    line_width: int = 2,
    depth_cm: float = 3.0,
    image_height_px: int = 512,
    min_length_mm: float = 1.0,
    max_length_mm: float = 7.0,
    line_length_weight: float = 1,
    font_path: str = "arial.ttf",
    font_size: int = 16,
    background_padding: int = 5,
    search_range: int = 5,
    deviation_threshold: float = 0.2
) -> Tuple[Image.Image, List[float]]:
    """
    在圖片上繪製垂直線條並標註其長度（毫米）。
    最後刪除與平均長度差異過大的線條。

    Args:
        image: 要繪製的原始圖片
        mask_np: 遮罩陣列，用於確定線條的位置
        num_lines: 要繪製的垂直線條數量
        line_color: 線條顏色，RGB格式
        line_width: 線條寬度（像素）
        depth_cm: 深度（公分），用於計算實際長度
        image_height_px: 圖片高度（像素）
        min_length_mm: 最小可接受的線條長度（毫米）
        max_length_mm: 最大可接受的線條長度（毫米）
        line_length_weight: 線條長度權重，用於調整結果
        font_path: 字型檔案路徑
        font_size: 字型大小
        background_padding: 文字背景的內邊距
        search_range: 搜尋遮罩範圍的像素數
        deviation_threshold: 允許的最大偏差比例（預設20%）

    Returns:
        image (Image.Image): 繪製完成的影像（RGB 模式）。
        line_lengths (List[float]): 所有繪製線條的實際毫米長度。
    """

    # 計算像素到毫米的比例（1 cm = 10 mm）
    px_to_mm_ratio = (depth_cm * 10) / image_height_px

    # 確保遮罩中有非零點
    if not np.any(mask_np > 0):
        logger.debug("未找到遮罩。")
        return image, []

    # 找到遮罩範圍
    _, x_indices = np.nonzero(mask_np)
    left_x = x_indices.min()
    right_x = x_indices.max()

    # 若範圍過小，無法繪製指定數量的線條
    if right_x - left_x < num_lines + 1:
        logger.debug("範圍過小，無法繪製指定數量的線條。")
        return image, []

    # 為支援半透明效果，將圖片轉為 RGBA（僅轉換一次）
    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # 利用 np.linspace 產生線條的 x 座標（均勻分佈）
    line_x_positions = np.linspace(left_x, right_x, num_lines + 2, dtype=int)[1:-1]

    potential_lines = []  # 儲存符合初始條件的線條資訊

    # 逐個處理每一條線
    for line_x in line_x_positions:
        # 利用 find_mask_at_x 找到當前 x 座標的上、下 y 座標
        top_y, bottom_y = find_mask_at_x(mask_np, int(line_x), search_range=search_range)
        if top_y is None or bottom_y is None:
            continue

        pixel_length = bottom_y - top_y
        mm_length = pixel_length * px_to_mm_ratio * line_length_weight

        # 過濾僅保留長度在允許範圍內的線條
        if min_length_mm <= mm_length <= max_length_mm:
            potential_lines.append({
                'x': int(line_x),
                'top_y': top_y,
                'bottom_y': bottom_y,
                'mm_length': mm_length
            })

    if not potential_lines:
        logger.debug("在指定長度範圍內未找到線條。")
        return image.convert("RGB"), []

    # 收集所有潛在線條的長度，利用 np.array 加速操作
    lengths = np.array([line['mm_length'] for line in potential_lines])
    if deviation_threshold > 0:
        # 四捨五入到小數點後一位（使用 np.round）
        rounded_lengths = np.round(lengths, 1)
        unique_lengths, counts = np.unique(rounded_lengths, return_counts=True)
        mean_length = unique_lengths[np.argmax(counts)]
    else:
        mean_length = np.mean(lengths)

    # 定義允許的長度範圍
    lower_bound = mean_length * (1 - (deviation_threshold if deviation_threshold != 0 else 0.2))
    upper_bound = mean_length * (1 + (deviation_threshold if deviation_threshold != 0 else 0.2))

    # 過濾掉與平均長度差異過大的線條
    filtered_lines = [line for line in potential_lines if lower_bound <= line['mm_length'] <= upper_bound]
    if not filtered_lines:
        logger.debug("根據平均長度偏差過濾後沒有剩餘的線條。")
        return image.convert("RGB"), []

    # 收集過濾後線條的長度
    line_lengths: List[float] = [line['mm_length'] for line in filtered_lines]

    # 建立一個 overlay，用來一次性繪製所有文字背景
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # 記錄每條線的文字資訊，格式為 (text, (text_x, text_y), (text_width, text_height))
    text_infos = []
    for line in filtered_lines:
        line_x = line['x']
        top_y = line['top_y']
        bottom_y = line['bottom_y']
        mm_length = line['mm_length']

        # 繪製垂直線條
        draw.line([(line_x, top_y), (line_x, bottom_y)],
                  fill=line_color, width=line_width)

        # 文字標註內容
        length_text = f"{mm_length:.2f} mm"
        bbox = draw.textbbox((0, 0), length_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 計算文字位置：使其置中於線條上方 10 像素處
        text_x = line_x - text_width / 2
        text_y = top_y - text_height - 10

        # 邊界檢查
        text_x = max(0, min(image.width - text_width, text_x))
        text_y = max(0, text_y)

        text_infos.append((length_text, (text_x, text_y), (text_width, text_height)))

    # 在 overlay 上集中繪製所有文字背景（半透明矩形）
    for _, (text_x, text_y), (text_width, text_height) in text_infos:
        background_rect = [
            text_x - background_padding,
            text_y - background_padding,
            text_x + text_width + background_padding,
            text_y + text_height + background_padding
        ]
        overlay_draw.rectangle(background_rect, fill=(0, 0, 0, 128))

    # 合成 overlay 與原始圖片
    image = Image.alpha_composite(image, overlay)

    # 在合成後的圖片上繪製文字標註（確保文字在背景之上）
    draw = ImageDraw.Draw(image)
    for length_text, (text_x, text_y), _ in text_infos:
        draw.text((text_x, text_y), length_text, fill=(255, 255, 255), font=font)

    return image.convert("RGB"), line_lengths