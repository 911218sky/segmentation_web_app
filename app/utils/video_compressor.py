import shutil
import subprocess
from typing import Optional, Union, List


class VideoCompressor:
    """
    VideoCompressor：使用 ffmpeg 壓縮影片的簡單封裝器。

    預設參數對應（根據您提供的截圖）：
      - 输出格式: mp4
      - 視訊編碼器: libx264 (x264, software)
      - profile: baseline
      - preset: veryfast
      - 品質模式: CRF (quality) 預設 24.0（可改為 bitrate 模式）
      - 幀率: 24 fps
      - Keyframe(關鍵幀)間隔: 10 秒 -> GOP = fps * 10
      - 音訊編碼器: aac (LC)
      - 音訊位元率: 128 kbps
      - 取樣率: 48000 Hz
    --------------------------------------------------------------------
    注意：
      - 此程式組出 ffmpeg 命令並呼叫 subprocess 執行，會 block 直到完成。
      - 若要解析更精細的 x264 參數，可透過 x264-params（-x264-params）傳入。
    """

    def __init__(
        self,
        output_format: str = "mp4",
        video_codec: str = "libx264",
        profile: str = "baseline",       # baseline / main / high / ...
        preset: str = "veryfast",        # x264 preset
        tune: Optional[str] = None,      # e.g. 'film', 'animation', None -> screenshot shows 'none'
        quality_mode: str = "crf",       # 'crf' or 'bitrate'
        crf: float = 24.0,               # only when quality_mode == 'crf'
        video_bitrate: Optional[str] = None,  # e.g. '2000k' if using bitrate mode
        fps: float = 24.0,
        keyframe_interval_seconds: float = 10.0,
        cfr: bool = True,                # constant frame rate
        x264_zerolatency: bool = False,  # screenshot had "零延遲" checkbox
        x264_fastdecode: bool = False,   # screenshot had "快速解碼" checkbox
        audio_codec: str = "aac",
        audio_bitrate: str = "128k",
        audio_channels: Union[str, int] = "original",  # 'original', 'mono', 'stereo', '5.1', '7.1' or integer
        audio_sample_rate: int = 48000,
    ):
        self.output_format = output_format
        self.video_codec = video_codec
        self.profile = profile
        self.preset = preset
        self.tune = tune
        self.quality_mode = quality_mode
        self.crf = crf
        self.video_bitrate = video_bitrate
        self.fps = float(fps)
        self.keyframe_interval_seconds = float(keyframe_interval_seconds)
        self.cfr = cfr
        self.x264_zerolatency = x264_zerolatency
        self.x264_fastdecode = x264_fastdecode
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.audio_channels = audio_channels
        self.audio_sample_rate = audio_sample_rate

        # 檢查 ffmpeg 是否存在（不拋出例外，只是 warning 形式）
        if shutil.which("ffmpeg") is None:
            print("警告: 找不到 'ffmpeg' 可執行檔。請先安裝 ffmpeg 並加入 PATH。")

    def _channels_to_ac(self) -> Optional[int]:
        """將 audio_channels 轉成 ffmpeg 的 -ac 參數 (數字)"""
        if isinstance(self.audio_channels, int):
            return int(self.audio_channels)
        mapping = {
            "original": None,
            "mono": 1,
            "single": 1,
            "單聲道": 1,
            "stereo": 2,
            "立體聲": 2,
            "5.1": 6,
            "7.1": 8,
        }
        return mapping.get(str(self.audio_channels).lower(), None)

    def _build_x264_params(self, gop: int) -> Optional[str]:
        """建立 -x264-params 字串，包含 zerolatency / fastdecode / keyint (keyframe)"""
        parts: List[str] = []
        # keyint = GOP size (max interval between I-frames)
        if gop > 0:
            parts.append(f"keyint={gop}")  # x264 參數 keyint
        if self.x264_zerolatency:
            parts.append("zerolatency=1")
        if self.x264_fastdecode:
            parts.append("fastdecode=1")
        if not parts:
            return None
        return ":".join(parts)

    def build_command(self, input_path: str, output_path: str, overwrite: bool = True) -> List[str]:
        """
        建立 ffmpeg 的命令列（list 形式）
        """
        cmd: List[str] = ["ffmpeg", "-y" if overwrite else "-n", "-i", input_path]

        # video codec
        cmd += ["-c:v", self.video_codec]

        # profile
        if self.profile:
            cmd += ["-profile:v", self.profile]

        # preset
        if self.preset:
            cmd += ["-preset", self.preset]

        # tune (如果有)
        if self.tune:
            cmd += ["-tune", self.tune]

        # fps / CFR
        if self.fps:
            # -r 在輸出端強制輸出 fps
            cmd += ["-r", str(int(self.fps))]
            if self.cfr:
                # vsync cfr 用來盡量輸出固定幀率
                cmd += ["-vsync", "cfr"]

        # keyframe interval (GOP)
        # gop = fps * keyframe_interval_seconds
        gop = max(1, int(round(self.fps * self.keyframe_interval_seconds)))
        cmd += ["-g", str(gop)]

        # quality or bitrate
        if self.quality_mode == "crf":
            # 使用 CRF 品質（對應截圖的 Quality / e.g. 24.0）
            cmd += ["-crf", str(self.crf)]
        else:
            # 使用 bitrate 模式（平均位元率/目標位元率）
            if not self.video_bitrate:
                raise ValueError("video_bitrate 必須在 bitrate 模式下設定，例如 '2000k'")
            cmd += ["-b:v", self.video_bitrate]

        # x264 進階參數
        x264_params = self._build_x264_params(gop)
        if x264_params:
            cmd += ["-x264-params", x264_params]

        # audio
        if self.audio_codec:
            cmd += ["-c:a", self.audio_codec]
        if self.audio_bitrate:
            cmd += ["-b:a", self.audio_bitrate]
        ac = self._channels_to_ac()
        if ac is not None:
            cmd += ["-ac", str(ac)]
        if self.audio_sample_rate:
            cmd += ["-ar", str(int(self.audio_sample_rate))]

        # container / format
        # ffmpeg 會根據輸出副檔名自動設定某些參數，但仍可強制設定 format
        if self.output_format:
            cmd += ["-f", self.output_format]

        cmd += [output_path]
        return cmd

    def compress(
        self,
        input_path: str,
        output_path: str,
        overwrite: bool = True,
        dry_run: bool = False,
        quiet: bool = False,
        log_file: Optional[str] = None,
    ) -> int:
        """
        執行壓縮
        參數:
          - input_path: 輸入影片路徑
          - output_path: 輸出影片路徑
          - overwrite: True -> 覆蓋已存在的輸出檔
          - dry_run: True -> 不執行，只回傳要執行的命令 (並印出)
        回傳:
          ffmpeg 的 returncode (0 表示成功)
        """
        cmd = self.build_command(input_path, output_path, overwrite=overwrite)
        print("ffmpeg command:")
        print(" ".join(cmd))
        if dry_run:
            return 0

        if shutil.which("ffmpeg") is None:
            raise FileNotFoundError("找不到 ffmpeg 可執行檔，請先安裝 ffmpeg 並加入 PATH。")

        stdout_target = None
        stderr_target = None
        
        if log_file:
            # 若提供 log_file，寫入該檔案
            log_fh = open(log_file, "w", encoding="utf-8")
            stdout_target = log_fh
            stderr_target = log_fh
        elif quiet:
            # 若 quiet=True 且未提供 log_file，則把輸出丟棄
            stdout_target = subprocess.DEVNULL
            stderr_target = subprocess.DEVNULL
        else:
            # 不指定（None）: 繼承父程序的 stdout/stderr（會顯示在終端）
            stdout_target = None
            stderr_target = None

        # 執行 ffmpeg，直接把 stdout/stderr 打到目前終端顯示（可以根據需要改為捕獲）
        process = subprocess.Popen(cmd, stdout=stdout_target, stderr=stderr_target)
        process.wait()
        
        return process.returncode


if __name__ == "__main__":
    # 範例：使用預設設定進行壓縮
    compressor = VideoCompressor()

    # dry run（僅印出命令）
    cmd_return = compressor.compress(
      "downloads/ScreenRecording_06-09-2025 08-42-29_1.mp4",
      "downloads/test.mp4",
      overwrite=True,
      dry_run=False
    )
    print("dry_run return:", cmd_return)