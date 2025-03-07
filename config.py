"""
Configuration settings for the application.
"""
from typing import Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class ThreadingConfig:
    max_workers: int = 4  # Number of worker threads for parallel processing
    chunk_size: int = 2   # Number of images to process in each chunk
    batch_size: int = 4   # Batch size for model inference

@dataclass
class ModelConfig:
    filename: str = 'model_traced_v3.pt'
    fp_precision: str = 'fp16'  # 'fp16' or 'fp32'

@dataclass
class ImageConfig:
    size: Tuple[int, int] = (256, 256)
    channels: int = 1

@dataclass
class AppConfig:
    threading: ThreadingConfig = ThreadingConfig()
    model: ModelConfig = ModelConfig()
    image: ImageConfig = ImageConfig()

    @classmethod
    def get_default(cls) -> 'AppConfig':
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'threading': {
                'max_workers': self.threading.max_workers,
                'chunk_size': self.threading.chunk_size,
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