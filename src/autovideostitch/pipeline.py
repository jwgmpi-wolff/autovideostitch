from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .reports import write_reports
from .scenes import FrameMatch, SceneMatch, group_frame_matches
from .semantic import SemanticMatcher
from .video import VideoInfo, concatenate_clips, extract_clip, probe_video, sample_frames


@dataclass(frozen=True, slots=True)
class SearchOptions:
    sample_interval: float = 2.0
    threshold: float = 0.24
    merge_gap: float = 3.0
    padding: float = 2.0
    max_scenes: int = 80


def run_search(
    video_paths: list[Path],
    description: str,
    output_video: Path,
    options: SearchOptions = SearchOptions(),
    progress: Callable[[str, float], None] | None = None,
    reference_image: Path | None = None,
) -> list[SceneMatch]:
    notify = progress or (lambda _message, _fraction: None)
    if not video_paths:
        raise ValueError("Select at least one video file.")
    if not description.strip() and reference_image is None:
        raise ValueError("Enter a scene description or select a reference image.")
    if reference_image is not None and not reference_image.is_file():
        raise ValueError("The selected reference image does not exist.")
    if options.sample_interval <= 0 or not 0 <= options.threshold <= 1:
        raise ValueError("Sample interval must be positive and threshold must be between 0 and 1.")

    output_video = output_video.with_suffix(".mp4")
    output_video.parent.mkdir(parents=True, exist_ok=True)
    notify("Reading video metadata...", 0.02)
    videos = [probe_video(path) for path in video_paths]
    durations = {video.path: video.duration for video in videos}
    matcher = SemanticMatcher(lambda message: notify(message, 0.12))
    frame_matches: list[FrameMatch] = []

    with tempfile.TemporaryDirectory(prefix="auto-video-stitch-") as temporary:
        work = Path(temporary)
        for video_index, video in enumerate(videos):
            start_fraction = 0.1 + 0.55 * video_index / len(videos)
            notify(f"Sampling {video.path.name}...", start_fraction)
            samples = sample_frames(video, work / f"frames_{video_index:04d}", options.sample_interval)
            if not samples:
                continue
            scores = matcher.score(description, [path for path, _timestamp in samples], reference_image)
            frame_matches.extend(
                FrameMatch(video.path, timestamp, score)
                for (_path, timestamp), score in zip(samples, scores, strict=True)
                if score >= options.threshold
            )

        scenes = group_frame_matches(
            frame_matches,
            sample_interval=options.sample_interval,
            merge_gap=options.merge_gap,
            padding=options.padding,
            durations=durations,
        )
        scenes = _limit_scenes(scenes, options.max_scenes)
        if not scenes:
            raise RuntimeError("No matching scenes were found. Try a lower match threshold or a wider description.")

        clips: list[Path] = []
        video_by_path: dict[Path, VideoInfo] = {video.path: video for video in videos}
        for index, scene in enumerate(scenes):
            notify(f"Creating clip {index + 1} of {len(scenes)}...", 0.68 + 0.27 * index / len(scenes))
            clip = work / "clips" / f"clip_{index:04d}.mp4"
            extract_clip(video_by_path[scene.video_path], scene.start, scene.end, clip)
            clips.append(clip)

        notify("Stitching the result video...", 0.96)
        concatenate_clips(clips, output_video, work / "clips.txt")
        write_reports(scenes, description, output_video, reference_image)
    notify("Complete", 1.0)
    return scenes


def _limit_scenes(scenes: list[SceneMatch], maximum: int) -> list[SceneMatch]:
    if maximum <= 0 or len(scenes) <= maximum:
        return scenes
    selected = sorted(scenes, key=lambda scene: scene.score, reverse=True)[:maximum]
    return sorted(selected, key=lambda scene: (str(scene.video_path).lower(), scene.start))