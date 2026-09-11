"""AutoVideoStitch package."""

from .core import SceneFilter, stitch_clips, validate_clip_list, validate_scene_filter

__all__ = [
    "SceneFilter",
    "stitch_clips",
    "validate_clip_list",
    "validate_scene_filter",
    "__version__",
]
__version__ = "0.1.0"
