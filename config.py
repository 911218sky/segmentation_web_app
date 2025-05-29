from typing import Tuple, Dict, Any
from dataclasses import dataclass, field
import os

@dataclass
class ThreadingConfig:
    max_workers: int = os.cpu_count() // 2  # Number of worker threads for parallel processing
    batch_size: int = 4   # Batch size for model inference

@dataclass
class ModelConfig:
    model_dir: str = 'models'
    filename: str = 'model_trt_fp16_v4.ts'
    fp_precision: str = 'fp16'  # 'fp16' or 'fp32' or 'bf16'

@dataclass
class ImageConfig:
    size: Tuple[int, int] = (256, 256)
    channels: int = 1

@dataclass
class AppConfig:
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    image: ImageConfig = field(default_factory=ImageConfig)

    @classmethod
    def get_default(cls) -> 'AppConfig':
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'threading': {
                'max_workers': self.threading.max_workers,
                'batch_size': self.threading.batch_size,
            },
            'model': {
                'filename': self.model.filename,
                'fp_precision': self.model.fp_precision,
            },
            'image': {
                'size': self.image.size,
                'channels': self.image.channels,
            }
        }

# Default configuration
CONFIG = AppConfig.get_default() 