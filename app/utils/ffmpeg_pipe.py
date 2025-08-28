import subprocess
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from typing import Optional, Iterable, Union

class FFmpegPipe:
    """
    輕量級的 ffmpeg 管線輔助類別。
    範例：
        with FFmpegPipe(out_path, width, height, fps=30, preset="ultrafast", crf=28) as pipe:
            pipe.write_frame_from_canvas(canvas, fig)
            ...
    方法：
        write_frame_rgb_array(rgb)  # rgb: H x W x 3 uint8
        write_frame_from_canvas(canvas, fig, flip_y=False)
        close()  # flush 並等待結束
    """

    def __init__(
        self,
        out_path: Union[str, bytes],
        width: int,
        height: int,
        fps: int = 30,
        preset: Optional[str] = "ultrafast",
        crf: Optional[int] = 28,
        bitrate_kbps: Optional[int] = None,
        pixel_format: str = "rgb24",
        ffmpeg_exe: str = "ffmpeg",
        extra_args: Optional[Iterable[str]] = None,
        loglevel: str = "error",
    ):
        self.out_path = str(out_path)
        self.W = int(width)
        self.H = int(height)
        self.fps = int(fps)
        self.preset = preset
        self.crf = crf
        self.bitrate_kbps = bitrate_kbps
        self.pixel_format = pixel_format
        self.ffmpeg_exe = ffmpeg_exe
        self.proc = None
        self._extra_args = list(extra_args) if extra_args else []
        self._loglevel = loglevel
        self._start_process()

    def _start_process(self):
        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", self.pixel_format,
            "-s", f"{self.W}x{self.H}",
            "-r", str(self.fps),
            "-i", "-",
            "-an",
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-loglevel", self._loglevel,
        ]
        if self.preset:
            cmd += ["-preset", self.preset]
        if self.crf is not None:
            cmd += ["-crf", str(int(self.crf))]
        if (self.crf is None) and (self.bitrate_kbps is not None):
            cmd += ["-b:v", f"{int(self.bitrate_kbps)}k"]
        cmd += list(self._extra_args)
        cmd += [self.out_path]

        # 開啟子程序 - 使用 list 形式避免 shell=True
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write_frame_rgb_array(self, rgb: np.ndarray):
        """
        寫入一個影格，輸入為 HxWx3 的 uint8 RGB 陣列。
        確保資料為連續記憶體區塊，並寫入 ffmpeg 的 stdin。
        """
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("FFmpeg process not running.")
        if rgb.dtype != np.uint8:
            raise TypeError("rgb array must be uint8.")
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise ValueError("rgb array must have shape (H, W, 3).")
        h, w, _ = rgb.shape
        if (h != self.H) or (w != self.W):
            raise ValueError(f"rgb shape {(h,w)} doesn't match pipe size {(self.H, self.W)}.")
        # 轉成連續的 bytes 並寫入 stdin
        self.proc.stdin.write(np.ascontiguousarray(rgb).tobytes())

    def write_frame_from_canvas(self, canvas: FigureCanvas):
        """
        將 Matplotlib Agg canvas 轉換成 RGB bytes，並寫入 ffmpeg。
        """

        # 獲取 canvas 的 RGBA 資料
        arr = np.asarray(canvas.buffer_rgba())  # shape (H, W, 4)
        # arr 可能是唯讀的 view；取前 3 個通道並建立連續陣列
        rgb = arr[:, :, :3]
        self.write_frame_rgb_array(rgb)

    def close(self, check_returncode: bool = True):
        """
        關閉 stdin 並等待 ffmpeg 完成。
        """
        if self.proc is None:
            return
        try:
            if self.proc.stdin:
                try:
                    # 嘗試關閉 stdin（讓 ffmpeg 收到 EOF）
                    self.proc.stdin.close()
                except Exception:
                    pass
            if check_returncode:
                # 等待子程序結束並取得 returncode
                self.proc.wait()
        finally:
            rc = self.proc.returncode
            self.proc = None
            return rc

    # 支援上下文管理器
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 即使上游拋出例外也要嘗試關閉子程序
        try:
            self.close(check_returncode=(exc_type is None))
        except Exception:
            pass