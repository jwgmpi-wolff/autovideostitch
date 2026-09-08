from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FrameMatch:
    video_path: Path
    timestamp: float
    score: float


@dataclass(frozen=True, slots=True)
class SceneMatch:
    video_path: Path
    start: float
    end: float
    score: float


def group_frame_matches(
    matches: list[FrameMatch],
    *,
    sample_interval: float,
    merge_gap: float,
    padding: float,
    durations: dict[Path, float],
) -> list[SceneMatch]:
    """Merge nearby matching frames into padded scene ranges."""
    grouped: list[SceneMatch] = []
    by_video: dict[Path, list[FrameMatch]] = {}
    for match in matches:
        by_video.setdefault(match.video_path, []).append(match)

    for video_path, video_matches in by_video.items():
        ordered = sorted(video_matches, key=lambda item: item.timestamp)
        scene_start = ordered[0].timestamp
        scene_end = ordered[0].timestamp + sample_interval
        best_score = ordered[0].score

        for match in ordered[1:]:
            if match.timestamp - scene_end <= merge_gap:
                scene_end = match.timestamp + sample_interval
                best_score = max(best_score, match.score)
                continue

            grouped.append(
                _build_scene(video_path, scene_start, scene_end, best_score, padding, durations)
            )
            scene_start = match.timestamp
            scene_end = match.timestamp + sample_interval
            best_score = match.score

        grouped.append(
            _build_scene(video_path, scene_start, scene_end, best_score, padding, durations)
        )

    return sorted(grouped, key=lambda item: (str(item.video_path).lower(), item.start))


def _build_scene(
    video_path: Path,
    start: float,
    end: float,
    score: float,
    padding: float,
    durations: dict[Path, float],
) -> SceneMatch:
    duration = durations[video_path]
    return SceneMatch(
        video_path=video_path,
        start=max(0.0, start - padding),
        end=min(duration, end + padding),
        score=score,
    )