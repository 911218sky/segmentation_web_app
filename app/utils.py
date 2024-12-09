import math
from typing import Any, List, Optional, Tuple

import numpy as np
import numpy.typing as npt
import torch
import torchvision.transforms as transforms
from PIL import Image, ImageDraw, ImageFont
import torchvision.transforms.functional as T

from model import UNet3Plus

def infer_batch(
    image_paths: List[str],
    model: UNet3Plus,
    batch_size: int = 16,
    fp_precision: str = "fp32",
    num_lines: int = 10,
    line_color: Tuple[int, int, int] = (0, 255, 0),
    line_width: int = 2,
    depth_cm: float = 3.2,
    min_length_mm: float = 1.0,
    max_length_mm: float = 7.0,
    line_length_weight: float = 1,
    transform: Optional[transforms.Compose] = None,
    device: Optional[torch.device] = None,
) -> List[Tuple[Optional[Image.Image], Optional[Image.Image], List[float]]]:
    """
    批次推理多張圖片並返回處理後的圖片、僅包含線條的遮罩覆蓋圖片和線條長度列表。

    Args:
        image_paths (List[str]): 
            圖片的檔案路徑列表。必須提供有效的圖片路徑，以便函數能夠加載並處理圖片。

        model (nn.Module): 
            用於推理的預訓練模型。該模型應該是已經訓練好的分割模型實例，用於生成圖片的遮罩。

        batch_size (int, optional):
            每次在 GPU 上推理的圖片數量。預設為 16。

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

        transform (transforms.Compose, optional): 
            圖片的預處理轉換管道。若未提供，將使用預設的轉換，包括調整大小和轉換為張量。可以自定義轉換以適應不同的預處理需求。

        device (torch.device, optional): 
            運行模型的設備，可以是 CPU 或 GPU。若未提供，將自動選擇可用的 GPU（如果有），否則使用 CPU。

    Returns:
        List[Tuple[Optional[Image.Image], Optional[Image.Image], List[float], str]]: 
            返回一個列表，其中每個元素是一個包含四個元素的元組：
            1. 處理後的圖片，包含繪製的垂直線條和長度標註。如果處理失敗，為 `None`。
            2. 僅包含繪製線條的遮罩覆蓋圖片。如果處理失敗，為 `None`。
            3. 繪製的所有線條的長度列表，以毫米為單位。如果處理失敗，為空列表。
    """
    results = []
    total_images = len(image_paths)
    if total_images == 0:
        print("No images to process.")
        return results

    # 設置設備
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 設置模型精度
    model = model.to(device)
    if fp_precision == "fp16":
        model = model.half()
    elif fp_precision == "fp32":
        model = model.float()
    else:
        raise ValueError("無效的 `fp_precision` 值，請選擇 'fp16' 或 'fp32'。")

    # 設置模型為評估模式
    model.eval()

    # 定義預設轉換（保持寬高比）
    if transform is None:
        transform: T.Compose = T.Compose([
            T.Resize((256, 256)),  # 調整圖片大小為 256x256
            T.ToTensor(),          # 將圖片轉換為張量
        ])

    # 計算總批次數
    num_batches = math.ceil(total_images / batch_size)

    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_images)
        current_batch_paths = image_paths[start_idx:end_idx]

        # 加載和預處理當前批次的圖片
        batch_images = []
        batch_original_sizes = []
        valid_batch_indices = []
        for i, image_path in enumerate(current_batch_paths):
            try:
                original_image = Image.open(image_path).convert("RGB")
                original_width, original_height = original_image.size
                batch_original_sizes.append((original_width, original_height))
                transformed_image = transform(original_image)
                batch_images.append(transformed_image)
                valid_batch_indices.append(i)
            except Exception as e:
                print(f"Failed to load or transform image {image_path}: {e}")
                batch_original_sizes.append((None, None))
                batch_images.append(None)

        # 移除加載失敗的圖片
        valid_images = []
        valid_sizes = []
        valid_paths = []
        for idx_in_batch, img in enumerate(batch_images):
            if img is not None:
                valid_images.append(img)
                valid_sizes.append(batch_original_sizes[idx_in_batch])
                valid_paths.append(current_batch_paths[idx_in_batch])
            else:
                # 如果圖片加載失敗，記錄為 None
                results.append((None, None, []))

        if not valid_images:
            print(
                f"No valid images in batch {batch_idx + 1}/{num_batches}, skipping.")
            continue

        # 堆疊成批次張量
        input_tensor = torch.stack(valid_images).to(device)

        # 將圖像張量的精度與模型匹配
        if fp_precision == "fp16":
            input_tensor = input_tensor.half()
        elif fp_precision == "fp32":
            input_tensor = input_tensor.float()

        # 推理
        with torch.no_grad():
            output = model(input_tensor)
            # 將輸出轉換為0-1之間的值
            output = torch.sigmoid(output)
            # 生成遮罩
            masks = (output > 0.5).cpu().numpy().astype(np.uint8) * 255

        # 處理每張圖片在批次中的推理結果
        for i in range(len(valid_images)):
            mask = masks[i]
            original_width, original_height = valid_sizes[i]
            current_image_path = valid_paths[i]

            # 將遮罩轉回 PIL Image 並縮放回原始尺寸
            mask_pil = Image.fromarray(mask.squeeze()).resize(
                (original_width, original_height), Image.NEAREST)
            mask_np_resized = np.array(mask_pil)

            # 加載原始圖片
            try:
                original_image = Image.open(current_image_path).convert("RGB")
            except Exception as e:
                print(
                    f"Failed to load original image {current_image_path}: {e}")
                results.append((None, None, []))
                continue

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
                line_length_weight=line_length_weight
            )

            # 繪製遮罩
            image_with_mask = draw_mask(
                image=original_image.copy(), 
                mask_np=mask_np_resized,
                color=(*line_color, 200),
                threshold=0.5
            )

            # 添加結果
            results.append((image_with_lines, image_with_mask, line_lengths))

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

def draw_average_length(image: Image.Image, line_lengths: List[float]) -> Image.Image:
    """
    在圖片上繪製平均長度標註。

    Args:
        image (Image.Image): 
            處理後的圖片，包含繪製的垂直線條和長度標註。

        line_lengths (List[float]): 
            繪製的所有線條的長度列表，以毫米為單位。

    Returns:
        Image.Image: 
            繪製完成的圖片。
    """
    # 計算平均長度
    if not line_lengths:
        print(f"No line lengths provided for image")
        return image

    avg_length = sum(line_lengths) / len(line_lengths)
    avg_length_text = f"Average Length: {avg_length:.2f} mm"
    
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
    deviation_threshold: float = 0.2  # 允許的最大偏差比例（例如 0.2 表示 20%）
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
        line_length_weight: 線條長度權重，用於調整線條長度結果的影響
        font_path: 字型檔案路徑
        font_size: 字型大小
        background_padding: 文字背景的內邊距
        search_range: 搜尋遮罩範圍的像素數
        deviation_threshold: 允許的最大偏差比例（默認為 20%）

    Returns:
        image (Image.Image): 繪製完成的影像。
        line_lengths (List[float]): 所有繪製線條的實際毫米長度。
    """

    # 計算像素到毫米的比例（1 cm = 10 mm）
    px_to_mm_ratio = (depth_cm * 10) / image_height_px

    # 確保遮罩中有非零點
    if not np.any(mask_np > 0):
        print("No mask found.")
        return image, []

    # 找到遮罩範圍
    _, x_indices = np.nonzero(mask_np)
    left_x = x_indices.min()
    right_x = x_indices.max()

    # 若範圍過小，無法繪製指定數量的線條
    if right_x - left_x < num_lines + 1:
        print("Not enough space to draw the requested number of lines.")
        return image, []

    # 建立繪圖物件
    draw = ImageDraw.Draw(image)

    # 載入字型
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    # 計算線條的 x 位置（均勻分佈）
    interval = (right_x - left_x) / (num_lines + 1)
    line_x_positions = [int(round(left_x + (i + 1) * interval)) for i in range(num_lines)]

    # 收集所有符合初始條件的線條資訊
    potential_lines = []

    for line_x in line_x_positions:
        top_y, bottom_y = find_mask_at_x(mask_np, line_x, search_range=search_range)
        if top_y is None or bottom_y is None:
            # 無法找到適合的遮罩範圍，略過
            continue

        # 計算線條長度（以 mm 為單位）
        pixel_length = bottom_y - top_y
        mm_length = pixel_length * px_to_mm_ratio * line_length_weight

        # 若在指定範圍內，將線條資訊加入潛在列表
        if min_length_mm <= mm_length <= max_length_mm:
            potential_lines.append({
                'x': line_x,
                'top_y': top_y,
                'bottom_y': bottom_y,
                'mm_length': mm_length
            })

    if not potential_lines:
        print("No lines found within the specified length range.")
        return image, []

    # 計算平均長度
    lengths = [line['mm_length'] for line in potential_lines]
    mean_length = np.mean(lengths)

    # 定義允許的長度範圍
    lower_bound = mean_length * (1 - deviation_threshold)
    upper_bound = mean_length * (1 + deviation_threshold)

    # 過濾掉與平均長度偏差過大的線條
    filtered_lines = [line for line in potential_lines if lower_bound <= line['mm_length'] <= upper_bound]

    if not filtered_lines:
        print("No lines remain after filtering based on deviation from the mean length.")
        return image, []

    # 收集過濾後的線條長度
    line_lengths = [line['mm_length'] for line in filtered_lines]

    # 繪製過濾後的線條
    for line in filtered_lines:
        line_x = line['x']
        top_y = line['top_y']
        bottom_y = line['bottom_y']
        mm_length = line['mm_length']

        # 繪製垂直線條
        draw.line(
            [(line_x, top_y), (line_x, bottom_y)],
            fill=line_color,
            width=line_width
        )

        length_text = f"{mm_length:.2f} mm"
        bbox = draw.textbbox((0, 0), length_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 將文字顯示在線條上方 10 px
        text_x = line_x - text_width / 2
        text_y = top_y - text_height - 10

        # 邊界檢查
        text_x = max(0, min(image.width - text_width, text_x))
        text_y = max(0, text_y)

        # 繪製半透明背景矩形
        # 注意：PIL 不直接支持半透明矩形，需創建新圖層
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        background_rect = [
            text_x - background_padding,
            text_y - background_padding,
            text_x + text_width + background_padding,
            text_y + text_height + background_padding
        ]
        overlay_draw.rectangle(background_rect, fill=(0, 0, 0, 128))
        image = Image.alpha_composite(image.convert('RGBA'), overlay)

        # 繪製文字標註
        draw = ImageDraw.Draw(image)
        draw.text((text_x, text_y), length_text, fill=(255, 255, 255), font=font)

    return image.convert('RGB'), line_lengths