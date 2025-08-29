import streamlit as st
from typing import List, Tuple, Optional
import re

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
    在 Streamlit 中呈現時間區間編輯器，並回傳最終的區間列表。

    功能：
      - 輸入開始/結束時間（支援多種格式）
      - 新增、刪除單筆區間
      - 合併重疊區間 / 清除 / 匯出為可複製字串

    參數:
      session_key: 存放在 st.session_state 的 key（可同頁面多組使用）
      default: 預設區間列表

    回傳:
      List[ (start_s, end_s), ... ]（數值為 float 秒）
    """
    if default is None:
        default = []

    # 初始化 session state
    if session_key not in st.session_state:
        st.session_state[session_key] = list(default)

    st.markdown("### ⏱️ 設定影片處理區間（秒）")
    st.markdown(
        "輸入範例：`75`、`75.5`、`01:15` 或 `0:01:15`"
    )

    # 新增區間表單
    with st.form(key=f"{session_key}_add_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([1.4, 1.4, 0.6])
        with c1:
            start_raw = st.text_input("開始 (秒 或 hh:mm:ss)",
                                      placeholder="例如 75 或 00:01:15",
                                      key=f"{session_key}_start")
        with c2:
            end_raw = st.text_input("結束 (秒 或 hh:mm:ss)",
                                    placeholder="例如 100 或 00:01:40",
                                    key=f"{session_key}_end")
        with c3:
            add_btn = st.form_submit_button("➕ 新增區間")

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

    if not intervals:
        st.info("目前沒有任何區間。請在上方輸入並按「➕ 新增區間」。")
    else:
        for i, (s, e) in enumerate(list(intervals)):
            # 三欄：編號 / 主要文字 (時間 + 長度) / 操作按鈕
            col_idx, col_main, col_actions = st.columns([0.12, 1.8, 0.5])

            # 左側：醒目的編號
            col_idx.markdown(f"**{i+1}**")

            # 中間：開始→結束（大字）與次要行（顯示秒數與 mm:ss）
            duration_s = e - s
            col_main.markdown(
                f"**{_seconds_to_hms(s)} → {_seconds_to_hms(e)}**  \n"  # 主行（粗體）
                f"共 {duration_s:.2f} 秒"  # 次行（純文字）
            )

            # 右側：刪除按鈕（只顯示圖示，並提供說明）
            # 使用單一圖示按鈕讓列表看起來更簡潔
            if col_actions.button("🗑️", key=f"{session_key}_del_{i}", help="刪除此區間"):
                st.session_state[session_key].pop(i)
                st.rerun()

            # 每筆之後加一條分隔線 (最後一筆不加)
            if i < len(intervals) - 1:
              st.divider()

    # 批次操作區塊
    st.write("---")
    cA, cB = st.columns([1, 1])
    with cA:
        if cA.button("🔀 合併重疊區間"):
            st.session_state[session_key] = _merge_intervals(st.session_state[session_key])
            st.success("已合併重疊 / 相接的區間。")
    with cB:
        if cB.button("🧹 清除全部區間"):
          st.session_state[session_key] = []
          st.success("已清除全部。")

    # 最終回傳
    final_list: List[Tuple[float, float]] = [(float(s), float(e)) for s, e in st.session_state[session_key]]
    return final_list