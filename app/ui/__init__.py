from .canvas import canvas
from .video_intervals import video_intervals
from .model import model_section
from .settings import settings_section
from .parameters import parameters_section
from .language import language_selector

from .image import (
    upload_images,
    handle_image_processing,
    image_results,
    image_downloads,
)

from .video import (
    upload_video,
    handle_video_processing,
    video_results,
    video_downloads,
)

__all__ = [
    "canvas",
    "model_section",
    "settings_section",
    "parameters_section",
    "language_selector",
    
    # image
    "upload_images",
    "handle_image_processing",
    "image_results",
    "image_downloads",
    
    # video
    "video_intervals",
    "upload_video",
    "handle_video_processing",
    "video_results",
    "video_downloads",
]