from .image import batch_uniform_resize
from .image_gpu import batch_uniform_resize_cuda

__all__ = ["batch_uniform_resize", "batch_uniform_resize_cuda"]