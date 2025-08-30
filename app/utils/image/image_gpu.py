from pathlib import Path
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from config import TARGET_SIZE

@dataclass
class UniformResizeResult:
    resized_image: np.ndarray
    scale: float
    padding: Tuple[int, int]
    saved_path: Optional[Path] = None

def _to_bchw_uint8_device(image: np.ndarray, device: torch.device) -> torch.Tensor:
    """
    將 np.ndarray(H,W,C|1) 轉成 (1,C,H,W) 的 uint8 tensor，放到指定裝置。
    - 不做 /255 規模化，避免多餘計算；插值前再轉 float32。
    """
    if image.ndim == 2:  # 灰階 -> (H,W,1)
        image = image[:, :, None]
    arr = np.ascontiguousarray(image)  # 確保連續
    t = torch.from_numpy(arr)
    # 若是要上 CUDA，pin memory + non_blocking 會更快
    if device.type == "cuda":
        t = t.pin_memory().to(device, non_blocking=True)
    else:
        t = t.to(device)
    # (H,W,C) -> (1,C,H,W)
    return t.permute(2, 0, 1).unsqueeze(0).to(dtype=torch.uint8)

@torch.inference_mode()
def uniform_resize_and_pad_cuda(
    image: np.ndarray,
    target_size: Tuple[int, int] = TARGET_SIZE
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    用 PyTorch 在 GPU（若可用）完成等比縮放 + letterbox。
    回傳：padded numpy(BGR/灰階), scale, (pad_left, pad_top)
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    th = int(target_size[1])
    tw = int(target_size[0])

    h, w = image.shape[:2]
    scale = min(tw / w, th / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))

    pad_top    = (th - nh) // 2
    pad_bottom = th - nh - pad_top
    pad_left   = (tw - nw) // 2
    pad_right  = tw - nw - pad_left

    # 上傳成 (1,C,H,W) uint8
    bchw_u8 = _to_bchw_uint8_device(image, device=device)

    # 轉 float 做插值
    bchw_f = bchw_u8.to(dtype=torch.float32)

    # 雙線性插值到 (nh, nw)
    resized = F.interpolate(bchw_f, size=(nh, nw), mode="bilinear", align_corners=False)

    # pad：順序 (left, right, top, bottom)
    padded = F.pad(resized, (pad_left, pad_right, pad_top, pad_bottom), value=0)

    # 回到 uint8
    padded_u8 = padded.clamp_(0, 255).to(torch.uint8)

    # 轉回 numpy（H,W,C 或 H,W,1）
    np_out = padded_u8.squeeze(0).permute(1, 2, 0).contiguous().cpu().numpy()
    if np_out.shape[2] == 1:
        np_out = np_out[:, :, 0]  # 灰階保持 2D

    return np_out, scale, (pad_left, pad_top)


@torch.inference_mode()
def batch_uniform_resize_cuda(
    images: List[np.ndarray],
    target_size: Tuple[int, int] = TARGET_SIZE,
    *,
    save_dir: Optional[Union[str, Path]] = None,
    prefix: str = "resized_"
) -> List[UniformResizeResult]:
    """
    批次處理版本。維持原有回傳型別與欄位。
    注意：這裡仍逐張 loop（控制流程在 Python），但重運算在 PyTorch（GPU/CPU）執行。
    """
    out_dir: Optional[Path] = None
    if save_dir is not None:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    results: List[UniformResizeResult] = []
    for i, img in enumerate(images):
        padded, scale, padding = uniform_resize_and_pad_cuda(img, target_size)
        saved_path = None
        if out_dir is not None:
            p = out_dir / f"{prefix}{i:04d}.jpg"
            cv2.imwrite(str(p), padded)
            saved_path = p

        results.append(UniformResizeResult(
            resized_image=padded,
            scale=scale,
            padding=padding,
            saved_path=saved_path
        ))
    return results