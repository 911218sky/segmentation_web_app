import streamlit as st
import re
import pandas as pd
from typing import List, Tuple, Optional

def _parse_time_to_seconds(t: str) -> float:
    """
    將各種時間字串解析為秒數 (float)。

    支援格式：
      - 純數字（秒）: "75" 或 "75.5"
      - mm:ss 或 hh:mm:ss（各段可為多位數）: "01:15", "0:01:15", "1:02:03"

    參數:
        t: 要解析的字串

    回傳:
        float: 對應的秒數

    例外:
        ValueError: 當輸入為空字串或格式不符時拋出
    """
    s = str(t).strip()
    if s == "":
        raise ValueError("空字串")

    # 純秒數（整數或浮點數）
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)

    # 支援 mm:ss 或 hh:mm:ss（最多三段）
    parts = s.split(':')
    if not 1 < len(parts) <= 3:
        raise ValueError("時間格式錯誤 (請使用秒數或 mm:ss 或 hh:mm:ss)")

    # 反序：從秒、分、時做計算
    try:
        parts_num = [float(p) for p in parts[::-1]]
    except Exception:
        raise ValueError("時間段包含非法數字")

    seconds = 0.0
    # i=0 -> 秒, i=1 -> 分, i=2 -> 時
    for i, v in enumerate(parts_num):
        seconds += v * (60 ** i)
    return seconds


def _seconds_to_hms(sec: float) -> str:
    """
    將秒數（可含小數）轉為 "hh:mm:ss"（若小於 1 小時則回傳 "mm:ss"）。

    參數:
        sec: 秒數（float）

    回傳:
        格式化後的字串（e.g. "01:15" 或 "00:01:15"）
    """
    total_seconds = int(round(sec))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _merge_intervals(intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    合併重疊或相鄰的時間區間。

    參數:
        intervals: List of (start_s, end_s)

    回傳:
        已合併並排序的區間列表
    """
    if not intervals:
        return []

    # 先轉型並排序
    sorted_itv = sorted(((float(s), float(e)) for s, e in intervals), key=lambda x: x[0])
    merged: List[List[float]] = [[sorted_itv[0][0], sorted_itv[0][1]]]

    for s, e in sorted_itv[1:]:
        last = merged[-1]
        # 若起始小於等於上一個結束（或極小誤差），則合併
        if s <= last[1] + 1e-6:
            last[1] = max(last[1], e)
        else:
            merged.append([s, e])

    return [(float(a), float(b)) for a, b in merged]

# 渲染時間區間
def video_intervals(
    session_key: str = "video_intervals",
    default: Optional[List[Tuple[float, float]]] = None
) -> List[Tuple[float, float]]:
    """
    改良版：在 Streamlit 中呈現時間區間編輯器，降低每次互動造成的卡頓。
    - 使用單一 DataFrame 顯示區間（避免為每筆建立大量 widget）
    - 使用 multiselect + 單一刪除按鈕來刪除多筆
    - 新增表單使用 clear_on_submit=True（提交後清空欄位）
    - 支援合併 / 清除 / 匯出簡單文字
    """
    if default is None:
        default = []

    # 初始化 session state
    if session_key not in st.session_state:
        st.session_state[session_key] = list(default)

    st.markdown("### ⏱️ 設定影片處理區間（秒）")
    st.markdown("輸入範例：`75`、`75.5`、`01:15` 或 `0:01:15`")

    # 新增區間表單
    c1, c2, c3 = st.columns([1.6, 1.6, 0.6])
    with c1:
        start_raw = st.text_input("開始 (秒 或 hh:mm:ss)",
                                    placeholder="例如 75 或 00:01:15",
                                    key=f"{session_key}_start")
    with c2:
        end_raw = st.text_input("結束 (秒 或 hh:mm:ss)",
                                placeholder="例如 100 或 00:01:40",
                                key=f"{session_key}_end")
    with c3:
        add_btn = st.button("➕ 新增區間")
    if add_btn:
        try:
            s = _parse_time_to_seconds(start_raw)
            e = _parse_time_to_seconds(end_raw)
            if e <= s:
                st.error("結束時間必須大於開始時間。")
            else:
                st.session_state[session_key].append((s, e))
                st.success(f"已新增：{_seconds_to_hms(s)} → {_seconds_to_hms(e)} ({s:.2f}s → {e:.2f}s)")
        except Exception as ex:
            st.error(f"解析時間失敗：{ex}")

    st.write("---")
    st.markdown("#### 已加入的區間")

    intervals = st.session_state[session_key]

    # 若無區間直接顯示提示
    if not intervals:
        st.info("目前沒有任何區間。請在上方輸入並按「➕ 新增區間」。")
    else:
        # 建 DataFrame（只建一次）
        df = pd.DataFrame(intervals, columns=["start_s", "end_s"])
        df["duration_s"] = df["end_s"] - df["start_s"]
        df["start_hms"] = df["start_s"].apply(_seconds_to_hms)
        df["end_hms"] = df["end_s"].apply(_seconds_to_hms)
        df["label"] = df.apply(lambda r: f"{_seconds_to_hms(r.start_s)} → {_seconds_to_hms(r.end_s)} ({r.duration_s:.2f}s)", axis=1)

        # 若筆數很少，顯示完整 table；若很多則分頁顯示（每頁 25）
        MAX_PER_PAGE = 25
        n = len(df)
        if n <= MAX_PER_PAGE:
            st.dataframe(df[["label"]].rename(columns={"label": "區間 (點選以選取)"}), use_container_width=True)
            display_df = df
            start_idx = 0
        else:
            # 分頁控制
            pages = (n + MAX_PER_PAGE - 1) // MAX_PER_PAGE
            page = st.number_input("頁面", min_value=1, max_value=pages, value=1, step=1, key=f"{session_key}_page")
            start_idx = (page - 1) * MAX_PER_PAGE
            display_df = df.iloc[start_idx:start_idx + MAX_PER_PAGE]
            st.dataframe(display_df[["label"]].rename(columns={"label": f"區間 (第 {page}/{pages} 頁)"}), use_container_width=True)

        # 用單一 multiselect 來選擇要刪除的項目（減少 per-item buttons）
        options = {f"{start_idx + idx + 1}. {row.label}": start_idx + idx for idx, row in enumerate(display_df.itertuples())}
        sel = st.multiselect("選取要刪除的區間（可多選）", options=list(options.keys()), key=f"{session_key}_multisel")
        if st.button("🗑️ 刪除所選", key=f"{session_key}_del_btn"):
            if not sel:
                st.warning("請先選擇要刪除的區間。")
            else:
                # 計算要保留的 intervals
                del_indices = set(options[s] for s in sel)
                new_list = [iv for idx, iv in enumerate(intervals) if idx not in del_indices]
                st.session_state[session_key] = new_list
                st.success(f"已刪除 {len(del_indices)} 筆。")

        # 匯出 & 複製用文字顯示（方便一次複製）
        st.write("---")
        cA, cB = st.columns([1, 1])
        with cA:
            if st.button("🔀 合併重疊區間", key=f"{session_key}_merge_btn"):
                st.session_state[session_key] = _merge_intervals(st.session_state[session_key])
                st.success("已合併重疊 / 相接的區間。")
        with cB:
            if st.button("🧹 清除全部區間", key=f"{session_key}_clear_btn"):
                st.session_state[session_key] = []

    # 最終回傳
    final_list: List[Tuple[float, float]] = [(float(s), float(e)) for s, e in st.session_state[session_key]]
    return final_list