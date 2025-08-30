import subprocess
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from typing import Optional, Iterable, Union, Sequence

class FFmpegPipe:
    """
    輕量級的 ffmpeg 管線輔助類別（預設參照圖片設定）.

    預設：
      - 容器/封裝：mp4（依輸出副檔名）
      - 視訊編碼：H.264 (libx264)
      - Profile：baseline
      - Level：auto（不強制）
      - Preset：veryfast
      - 品質模式：CRF=24
      - 幀率：24 fps
      - 關鍵影格間隔：10 秒（= fps*10）
      - 像素格式：yuv420p
      - 音訊：AAC LC，128kbps，48kHz（僅當提供 audio_input 才加入；否則 -an）

    參考用法：
        with FFmpegPipe(out_path, width, height) as pipe:
            pipe.write_frame_from_canvas(canvas)
            ...
    """

    def __init__(
        self,
        out_path: Union[str, bytes],
        width: int,
        height: int,
        *,
        # 影像
        fps: int = 24,                         # 24
        preset: Optional[str] = "veryfast",    # veryfast
        crf: Optional[float] = 24.0,           # 24.0（品質模式）
        bitrate_kbps: Optional[int] = None,    # 若 crf 為 None 才會使用
        profile: str = "baseline",             # baseline
        level: Optional[str] = None,           # auto -> 不指定
        tune: Optional[Sequence[str]] = None,  # none（不加）; 可傳 ["fastdecode","zerolatency"]
        keyint_seconds: float = 10.0,          # 關鍵幀(秒)=10
        pixel_format_in: str = "rgb24",
        pixel_format_out: str = "yuv420p",
        # 音訊（只有在 audio_input 非 None 才會啟用）
        audio_input: Optional[Union[str, bytes]] = None,
        audio_codec: str = "aac",              # AAC
        audio_bitrate_kbps: int = 128,         # 128 kbps
        audio_sample_rate: int = 48000,        # 48000 Hz
        audio_channels: Optional[int] = None,  # 預設/立體聲；None=不強制
        # 其他
        ffmpeg_exe: str = "ffmpeg",
        extra_args: Optional[Iterable[str]] = None,
        loglevel: str = "error",
    ):
        self.out_path = str(out_path)
        self.W = int(width)
        self.H = int(height)
        self.fps = int(fps)
        self.preset = preset
        self.crf = None if crf is None else float(crf)
        self.bitrate_kbps = None if bitrate_kbps is None else int(bitrate_kbps)
        self.profile = profile
        self.level = level
        self.tune = list(tune) if tune else None
        self.keyint_seconds = float(keyint_seconds)
        self.pixel_format_in = pixel_format_in
        self.pixel_format_out = pixel_format_out

        self.audio_input = None if audio_input is None else str(audio_input)
        self.audio_codec = audio_codec
        self.audio_bitrate_kbps = int(audio_bitrate_kbps)
        self.audio_sample_rate = int(audio_sample_rate)
        self.audio_channels = audio_channels

        self.ffmpeg_exe = ffmpeg_exe
        self.proc = None
        self._extra_args = list(extra_args) if extra_args else []
        self._loglevel = loglevel
        self._start_process()

    def _start_process(self):
        # 輸入（rawvideo 管線）
        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", self.pixel_format_in,
            "-s", f"{self.W}x{self.H}",
            "-r", str(self.fps),     # 輸入幀率
            "-i", "-",               # 由 stdin 收原始影像
        ]

        # 可選音訊輸入
        if self.audio_input is not None:
            cmd += ["-i", self.audio_input]

        # 視訊輸出參數（x264）
        cmd += [
            "-vcodec", "libx264",
            "-pix_fmt", self.pixel_format_out,
            "-profile:v", self.profile,
            "-loglevel", self._loglevel,
        ]
        # level：auto -> 不加；如果指定就加
        if self.level:
            cmd += ["-level", str(self.level)]

        # preset
        if self.preset:
            cmd += ["-preset", self.preset]

        # 品質模式：預設 CRF 24；若 crf=None 且 bitrate_kbps 有值，改用 CBR/VBR
        if self.crf is not None:
            cmd += ["-crf", str(int(self.crf))]
        elif self.bitrate_kbps is not None:
            cmd += ["-b:v", f"{self.bitrate_kbps}k"]

        # 關鍵影格（10 秒）
        if self.keyint_seconds and self.keyint_seconds > 0:
            g = max(1, int(round(self.fps * self.keyint_seconds)))
            # 同時把最小 keyint 設為 fps（約 1 秒）
            x264_params = f"keyint={g}:min-keyint={self.fps}"
            cmd += ["-g", str(g), "-x264-params", x264_params]

        # tune（若有）
        if self.tune:
            cmd += ["-tune", ",".join(self.tune)]

        # 音訊輸出
        if self.audio_input is None:
            cmd += ["-an"]  # 沒有音源就關閉音訊
        else:
            cmd += ["-c:a", self.audio_codec, "-b:a", f"{self.audio_bitrate_kbps}k",
                    "-ar", str(self.audio_sample_rate)]
            if self.audio_channels:
                cmd += ["-ac", str(self.audio_channels)]

        # 其他額外參數 & 輸出路徑
        cmd += list(self._extra_args)
        cmd += [self.out_path]

        # 開啟子程序
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write_frame_rgb_array(self, rgb: np.ndarray):
        """寫入一個影格，輸入為 HxWx3 的 uint8 RGB 陣列。"""
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("FFmpeg process not running.")
        if rgb.dtype != np.uint8:
            raise TypeError("rgb array must be uint8.")
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise ValueError("rgb array must have shape (H, W, 3).")
        h, w, _ = rgb.shape
        if (h != self.H) or (w != self.W):
            raise ValueError(f"rgb shape {(h,w)} doesn't match pipe size {(self.H, self.W)}.")
        self.proc.stdin.write(np.ascontiguousarray(rgb).tobytes())

    def write_frame_from_canvas(self, canvas: FigureCanvas):
        """將 Matplotlib Agg canvas 轉為 RGB bytes 並寫入 ffmpeg。"""
        arr = np.asarray(canvas.buffer_rgba())  # (H, W, 4)
        rgb = arr[:, :, :3]
        self.write_frame_rgb_array(rgb)

    def close(self, check_returncode: bool = True):
        """關閉 stdin 並等待 ffmpeg 完成。"""
        if self.proc is None:
            return
        try:
            if self.proc.stdin:
                try:
                    self.proc.stdin.close()  # EOF
                except Exception:
                    pass
            if check_returncode:
                self.proc.wait()
        finally:
            rc = self.proc.returncode
            self.proc = None
            return rc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.close(check_returncode=(exc_type is None))
        except Exception:
            pass