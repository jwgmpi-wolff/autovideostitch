"""Core stitching utilities for AutoVideoStitch."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


SCENE_FILTER_MODES = ("none", "face", "image", "text")


@dataclass(frozen=True)
class SceneFilter:
    """Validated scene-filter settings for a stitch plan."""

    mode: str = "none"
    value: str = ""


def validate_scene_filter(mode: str, value: str = "") -> SceneFilter:
    """Validate and normalize scene-filter settings."""
    normalized_mode = str(mode).strip().lower()
    normalized_value = str(value).strip()
    if normalized_mode not in SCENE_FILTER_MODES:
        raise ValueError(f"unknown scene filter: {mode}")
    if normalized_mode == "image":
        if not normalized_value:
            raise ValueError("select a reference image for image detection")
        if not Path(normalized_value).is_file():
            raise ValueError("the reference image does not exist")
    elif normalized_mode == "text":
        if not normalized_value:
            raise ValueError("enter a text description for the AI filter")
    elif normalized_mode in ("none", "face"):
        normalized_value = ""
    return SceneFilter(normalized_mode, normalized_value)


def validate_clip_list(clips: Sequence[str | Path]) -> List[str]:
    """Return normalized clip paths and reject empty or blank inputs."""
    if clips is None:
        raise ValueError("clips must not be None")

    normalized = []
    for clip in clips:
        if clip is None:
            raise ValueError("clip entries must not be None")
        value = str(clip).strip()
        if not value:
            raise ValueError("clip entries must not be empty")
        normalized.append(value)

    if not normalized:
        raise ValueError("at least one clip must be provided")

    return normalized


def stitch_clips(
    clips: Sequence[str | Path],
    output_path: str | Path | None = None,
    scene_filter: SceneFilter | None = None,
) -> list[str]:
    """Return the list of clip paths to stitch.

    The function intentionally avoids requiring heavy media-processing libraries so the
    package remains installable in minimal environments. It validates input and returns
    the normalized clip list, which callers can then use to build their video pipeline.
    """
    normalized = validate_clip_list(clips)
    if scene_filter is not None:
        validate_scene_filter(scene_filter.mode, scene_filter.value)
    if output_path is None:
        output_path = "stitched_output.mp4"
    output_path = str(output_path)
    return [*normalized, output_path]
