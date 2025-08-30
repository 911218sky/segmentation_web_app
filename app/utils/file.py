from typing import Optional
from pathlib import Path
import time

from streamlit.runtime.uploaded_file_manager import UploadedFile
from config import TEMP_DIR

def save_uploaded_to_dir(uploaded_file: UploadedFile, base_dir: Path = TEMP_DIR) -> Path:
    """把 st 上傳的檔案寫到暫存檔並回傳 Path"""
    if not base_dir.exists():
        raise FileNotFoundError(f"資料夾不存在: {base_dir}")
    
    tmp_file = base_dir / f"{uploaded_file.name}"
    
    if tmp_file.exists():
        print(f"file is exists, skip save {tmp_file}")
        return tmp_file
    
    try:
        # 如果之前讀過 upload，這裡先回到開頭
        uploaded_file.seek(0)
    except Exception:
        pass
    
    with open(tmp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return tmp_file

def clean_folder(
    folder: Path,
    max_items: Optional[int] = None,
    max_age_days: Optional[int] = None,
) -> None:
    """
    清理指定資料夾：
      - 如果指定 max_items，則只保留最新的 max_items 個檔案，舊檔案會被刪除。
      - 如果指定 max_age_days，則刪除所有超過該天數的檔案。

    Args:
        folder: 要清理的資料夾路徑。
        max_items: 保留的最新檔案數量，舊檔案超出部分會被刪除。
        max_age_days: 檔案最長保存天數，超過此天數的檔案會被刪除。
    """
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"資料夾不存在或不是資料夾：{folder}")

    # 取得所有檔案（不含資料夾）
    files = [p for p in folder.iterdir() if p.is_file()]
    # 依照修改時間，由新到舊排序
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    to_delete = set()

    # 處理 max_items
    if max_items is not None and len(files) > max_items:
        for f in files[max_items:]:
            to_delete.add(f)

    # 處理 max_age_days
    if max_age_days is not None:
        now = time.time()
        cutoff = now - max_age_days * 86400
        for f in files:
            if f.stat().st_mtime < cutoff:
                to_delete.add(f)

    if not to_delete:
        return

    # 列出將要刪除的檔案
    print("以下檔案將被刪除：")
    for f in sorted(to_delete, key=lambda p: p.stat().st_mtime):
        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime))
        print(f"  {f.name}  (最後修改：{mtime})")

    for f in to_delete:
        try:
            f.unlink()
        except Exception as e:
            print(f"無法刪除 {f.name}：{e}")