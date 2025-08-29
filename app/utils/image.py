from pathlib import Path
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass

import cv2
import numpy as np

from config import TARGET_SIZE

@dataclass
class UniformResizeResult:
    """單張影像等比縮放後的資訊"""
    resized_image: np.ndarray
    scale: float
    padding: Tuple[int, int]
    saved_path: Optional[Path] = None 

def uniform_resize_and_pad(
    image: np.ndarray,
    target_size: Tuple[int, int] = TARGET_SIZE
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    等比縮放並填黑邊到指定大小。

    Args:
        image: 原始 BGR/灰階 np.ndarray
        target_size: (width, height)

    Returns:
        padded: 處理後影像
        scale: 縮放比例
        padding: (pad_left, pad_top)
    """
    h, w = image.shape[:2]
    tw, th = target_size
    scale = min(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)

    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)

    pad_top = (th - nh) // 2
    pad_bottom = th - nh - pad_top
    pad_left = (tw - nw) // 2
    pad_right = tw - nw - pad_left

    padded = cv2.copyMakeBorder(
        resized,
        pad_top, pad_bottom, pad_left, pad_right,
        borderType=cv2.BORDER_CONSTANT,
        value=[0, 0, 0]
    )
    return padded, scale, (pad_left, pad_top)

def batch_uniform_resize(
    images: List[np.ndarray],
    target_size: Tuple[int, int] = TARGET_SIZE,
    *,
    save_dir: Optional[Union[str, Path]] = None,
    prefix: str = "resized_"
) -> List[UniformResizeResult]:
    """
    批量對多張影像做等比縮放 + 黑邊填充，可選擇性儲存到磁碟。

    Args:
        images:      原始影像列表（BGR 或灰階）
        target_size: 目標大小 (width, height)
        save_dir:    若傳入 Path/str，結果會依序儲存在此目錄；若為 None，僅保留在記憶體
        prefix:      儲存時的檔名前綴

    Returns:
        List[UniformResizeResult]: 每張影像的處理結果與 metadata
    """
    results: List[UniformResizeResult] = []

    out_dir: Optional[Path]
    if save_dir is not None:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    for idx, img in enumerate(images):
        padded, scale, padding = uniform_resize_and_pad(img, target_size)

        saved_path: Optional[Path]
        if out_dir is not None:
            fname = f"{prefix}{idx:04d}.jpg"
            p = out_dir / fname
            cv2.imwrite(str(p), padded)
            saved_path = p
        else:
            saved_path = None

        results.append(UniformResizeResult(
            resized_image=padded,
            scale=scale,
            padding=padding,
            saved_path=saved_path
        ))

    return results