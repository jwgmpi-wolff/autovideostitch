"""Local scene detection and video rendering pipeline."""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Sequence

from .core import SceneFilter, validate_clip_list, validate_scene_filter


CLIP_MODEL_ID = "openai/clip-vit-base-patch32"
ProgressCallback = Callable[[float, str], None]


class VideoProcessingError(RuntimeError):
    """Raised when scene analysis or video encoding cannot complete."""


@dataclass(frozen=True)
class VideoSegment:
    clip_path: str
    start: float
    end: float


def _notify(callback: ProgressCallback | None, value: float, message: str) -> None:
    if callback is not None:
        callback(max(0.0, min(1.0, value)), message)


def _merge_times(
    clip_path: str,
    times: Sequence[float],
    duration: float,
    sample_interval: float,
    padding: float,
) -> list[VideoSegment]:
    ranges = [
        (max(0.0, time - padding), min(duration, time + sample_interval + padding))
        for time in times
    ]
    if not ranges:
        return []

    merged: list[tuple[float, float]] = [ranges[0]]
    for start, end in ranges[1:]:
        previous_start, previous_end = merged[-1]
        if start <= previous_end + 0.05:
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return [VideoSegment(clip_path, start, end) for start, end in merged]


@lru_cache(maxsize=1)
def _load_clip_model() -> tuple[object, object]:
    try:
        from transformers import CLIPModel, CLIPProcessor

        processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID, use_fast=False)
        model = CLIPModel.from_pretrained(CLIP_MODEL_ID)
        model.eval()
    except (OSError, RuntimeError, ImportError) as exc:
        raise VideoProcessingError(
            "The CLIP model could not be loaded. Check your internet connection for "
            "the first download, then try again."
        ) from exc
    return model, processor


def _normalized_features(features: object) -> object:
    return features / features.norm(p=2, dim=-1, keepdim=True)


def _create_clip_scorer(scene_filter: SceneFilter) -> Callable[[object], float]:
    try:
        import cv2
        import torch
        from PIL import Image
    except ImportError as exc:
        raise VideoProcessingError("The local AI runtime is not installed.") from exc

    model, processor = _load_clip_model()
    with torch.inference_mode():
        if scene_filter.mode == "text":
            inputs = processor(
                text=[f"a photo of {scene_filter.value}"],
                return_tensors="pt",
                padding=True,
            )
            query_features = _normalized_features(model.get_text_features(**inputs))
        else:
            reference = Image.open(scene_filter.value).convert("RGB")
            inputs = processor(images=reference, return_tensors="pt")
            query_features = _normalized_features(model.get_image_features(**inputs))

    def score(frame: object) -> float:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        with torch.inference_mode():
            inputs = processor(images=image, return_tensors="pt")
            frame_features = _normalized_features(model.get_image_features(**inputs))
            return float((frame_features @ query_features.T).item())

    return score


def _create_face_scorer() -> Callable[[object], float]:
    try:
        import cv2
    except ImportError as exc:
        raise VideoProcessingError("The local vision runtime is not installed.") from exc

    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        raise VideoProcessingError("The bundled face detector could not be loaded.")

    def score(frame: object) -> float:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40),
        )
        if len(faces) == 0:
            return 0.0
        frame_area = float(gray.shape[0] * gray.shape[1])
        largest_face = max(width * height for _x, _y, width, height in faces)
        area_score = min(1.0, largest_face / frame_area * 8.0)
        count_score = min(0.25, (len(faces) - 1) * 0.05)
        return min(1.0, area_score + count_score)

    return score


def _description_requests_people(description: str) -> bool:
    terms = (
        "baby",
        "boy",
        "child",
        "children",
        "crowd",
        "face",
        "girl",
        "man",
        "people",
        "person",
        "portrait",
        "woman",
    )
    words = set(re.findall(r"[a-z]+", description.lower()))
    return any(term in words for term in terms)


def _score_threshold(scores: Sequence[float], mode: str) -> float:
    if not scores:
        raise VideoProcessingError("No video frames could be analyzed.")
    ordered = sorted(scores)
    maximum = ordered[-1]
    minimum_confidence = {"face": 0.01, "image": 0.68, "text": 0.22}[mode]
    if maximum < minimum_confidence:
        raise VideoProcessingError("No scenes confidently matched the selected AI filter.")

    percentile_index = max(0, math.ceil(len(ordered) * 0.8) - 1)
    prominence = {"face": 0.15, "image": 0.06, "text": 0.025}[mode]
    return max(
        minimum_confidence,
        ordered[percentile_index],
        maximum - prominence,
    )


def detect_segments(
    clips: Sequence[str | Path],
    scene_filter: SceneFilter,
    *,
    sample_interval: float = 1.0,
    padding: float = 0.5,
    progress: ProgressCallback | None = None,
) -> list[VideoSegment]:
    """Analyze clips and return time ranges matching the selected scene filter."""
    clip_paths = validate_clip_list(clips)
    selected_filter = validate_scene_filter(scene_filter.mode, scene_filter.value)
    if sample_interval <= 0:
        raise ValueError("sample interval must be greater than zero")
    if padding < 0:
        raise ValueError("padding must not be negative")

    for clip_path in clip_paths:
        if not Path(clip_path).is_file():
            raise ValueError(f"video clip does not exist: {clip_path}")

    if selected_filter.mode == "none":
        return _full_clip_segments(clip_paths)

    try:
        import cv2
    except ImportError as exc:
        raise VideoProcessingError("The local vision runtime is not installed.") from exc

    face_scorer = (
        _create_face_scorer()
        if selected_filter.mode == "face"
        or (
            selected_filter.mode == "text"
            and _description_requests_people(selected_filter.value)
        )
        else None
    )
    clip_scorer = (
        _create_clip_scorer(selected_filter) if selected_filter.mode != "face" else None
    )
    samples_by_clip: dict[str, list[tuple[float, float]]] = {}
    durations: dict[str, float] = {}
    for clip_index, clip_path in enumerate(clip_paths):
        capture = cv2.VideoCapture(clip_path)
        if not capture.isOpened():
            raise VideoProcessingError(f"could not open video clip: {clip_path}")
        try:
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if fps <= 0 or frame_count <= 0:
                raise VideoProcessingError(f"could not determine video duration: {clip_path}")
            duration = frame_count / fps
            durations[clip_path] = duration
            sample_count = max(1, math.ceil(duration / sample_interval))
            samples: list[tuple[float, float]] = []
            for sample_index in range(sample_count):
                timestamp = min(sample_index * sample_interval, max(0.0, duration - 0.001))
                capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
                available, frame = capture.read()
                if available:
                    if selected_filter.mode != "face" and clip_scorer is None:
                        raise VideoProcessingError("The semantic scene scorer is unavailable.")
                    semantic_score = clip_scorer(frame) if clip_scorer is not None else 0.0
                    face_score = face_scorer(frame) if face_scorer is not None else 0.0
                    if selected_filter.mode == "face":
                        combined_score = face_score
                    elif face_scorer is not None:
                        combined_score = semantic_score + face_score * 0.04
                    else:
                        combined_score = semantic_score
                    samples.append((timestamp, combined_score))
                overall = (clip_index + (sample_index + 1) / sample_count) / len(clip_paths)
                _notify(progress, overall * 0.7, f"Analyzing {Path(clip_path).name}")
            samples_by_clip[clip_path] = samples
        finally:
            capture.release()

    all_scores = [
        score for samples in samples_by_clip.values() for _timestamp, score in samples
    ]
    threshold = _score_threshold(all_scores, selected_filter.mode)
    segments: list[VideoSegment] = []
    for clip_path in clip_paths:
        matched_times = [
            timestamp
            for timestamp, score in samples_by_clip[clip_path]
            if score >= threshold
        ]
        segments.extend(
            _merge_times(
                clip_path,
                matched_times,
                durations[clip_path],
                sample_interval,
                padding,
            )
        )

    if not segments:
        raise VideoProcessingError("No scenes matched the selected AI filter.")
    return segments


def _full_clip_segments(clip_paths: Sequence[str]) -> list[VideoSegment]:
    try:
        import cv2
    except ImportError as exc:
        raise VideoProcessingError("The local vision runtime is not installed.") from exc

    segments: list[VideoSegment] = []
    for clip_path in clip_paths:
        capture = cv2.VideoCapture(clip_path)
        if not capture.isOpened():
            raise VideoProcessingError(f"could not open video clip: {clip_path}")
        try:
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if fps <= 0 or frame_count <= 0:
                raise VideoProcessingError(f"could not determine video duration: {clip_path}")
            segments.append(VideoSegment(clip_path, 0.0, frame_count / fps))
        finally:
            capture.release()
    return segments


def _ffmpeg_executable() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise VideoProcessingError("The bundled FFmpeg runtime is unavailable.") from exc


def _run_ffmpeg(command: Sequence[str]) -> str:
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=flags,
        check=False,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip()[-2000:]
        raise VideoProcessingError(f"FFmpeg failed while creating the video:\n{details}")
    return completed.stderr


def _has_audio(ffmpeg: str, clip_path: str) -> bool:
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", clip_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=flags,
        check=False,
    )
    return re.search(r"Stream #\S+.*Audio:", completed.stderr) is not None


def _ensure_free_space(output: Path, segments: Sequence[VideoSegment]) -> None:
    duration = sum(segment.end - segment.start for segment in segments)
    required = max(100 * 1024 * 1024, math.ceil(duration * 2_000_000))
    available = shutil.disk_usage(output.parent).free
    if output.exists():
        available += output.stat().st_size
    if available < required:
        raise VideoProcessingError(
            f"Not enough free space on {output.drive or output.parent}. "
            f"Approximately {required / (1024**3):.1f} GB is required, but only "
            f"{available / (1024**3):.1f} GB is available. Choose an output folder "
            "on a drive with more free space."
        )


def _build_filter_graph(
    segments: Sequence[VideoSegment],
    input_indexes: dict[str, int],
    audio_inputs: dict[str, bool],
) -> str:
    video_filter = (
        "scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p"
    )
    filters: list[str] = []
    concat_inputs: list[str] = []
    for segment_index, segment in enumerate(segments):
        input_index = input_indexes[segment.clip_path]
        start = f"{segment.start:.6f}"
        end = f"{segment.end:.6f}"
        duration = f"{segment.end - segment.start:.6f}"
        filters.append(
            f"[{input_index}:v:0]trim=start={start}:end={end},"
            f"setpts=PTS-STARTPTS,{video_filter}[v{segment_index}]"
        )
        if audio_inputs[segment.clip_path]:
            filters.append(
                f"[{input_index}:a:0]atrim=start={start}:end={end},"
                "asetpts=PTS-STARTPTS,aresample=48000,"
                f"aformat=sample_rates=48000:channel_layouts=stereo[a{segment_index}]"
            )
        else:
            filters.append(
                f"anullsrc=r=48000:cl=stereo,atrim=duration={duration},"
                f"asetpts=PTS-STARTPTS[a{segment_index}]"
            )
        concat_inputs.append(f"[v{segment_index}][a{segment_index}]")
    filters.append(
        f"{''.join(concat_inputs)}concat=n={len(segments)}:v=1:a=1[outv][outa]"
    )
    return ";\n".join(filters)


def _render_segments(
    ffmpeg: str,
    segments: Sequence[VideoSegment],
    output: Path,
) -> None:
    unique_clips = list(dict.fromkeys(segment.clip_path for segment in segments))
    input_indexes = {clip_path: index for index, clip_path in enumerate(unique_clips)}
    audio_inputs = {clip_path: _has_audio(ffmpeg, clip_path) for clip_path in unique_clips}
    filter_graph = _build_filter_graph(segments, input_indexes, audio_inputs)
    suffix = f".{os.getpid()}.partial"
    partial_output = output.with_name(f"{output.stem}{suffix}{output.suffix}")
    filter_script = output.with_name(f"{output.stem}{suffix}.filters.txt")
    filter_script.write_text(filter_graph, encoding="utf-8")
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    for clip_path in unique_clips:
        command.extend(["-i", clip_path])
    command.extend(
        [
            "-filter_complex_script",
            str(filter_script),
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(partial_output),
        ]
    )
    try:
        _run_ffmpeg(command)
        os.replace(partial_output, output)
    finally:
        filter_script.unlink(missing_ok=True)
        partial_output.unlink(missing_ok=True)


def render_video(
    clips: Sequence[str | Path],
    output_path: str | Path,
    scene_filter: SceneFilter | None = None,
    *,
    progress: ProgressCallback | None = None,
) -> Path:
    """Detect matching scenes and encode them into a stitched MP4 video."""
    selected_filter = scene_filter or SceneFilter()
    normalized_output = str(output_path).strip()
    if not normalized_output:
        raise ValueError("output path must not be empty")
    output = Path(normalized_output)
    if output.suffix.lower() != ".mp4":
        raise ValueError("output path must use the .mp4 extension")
    output.parent.mkdir(parents=True, exist_ok=True)

    segments = detect_segments(clips, selected_filter, progress=progress)
    _notify(progress, 0.7, f"Preparing {len(segments)} matching scene(s)")
    _ensure_free_space(output, segments)
    ffmpeg = _ffmpeg_executable()
    _notify(progress, 0.75, f"Encoding {len(segments)} matching scene(s)")
    _render_segments(ffmpeg, segments, output)
    _notify(progress, 0.98, "Finalizing video")
    _notify(progress, 1.0, "Video complete")
    return output
