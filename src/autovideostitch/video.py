from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}


@dataclass(frozen=True, slots=True)
class VideoInfo:
    path: Path
    duration: float
    has_audio: bool


def find_tool(name: str) -> str:
    executable = f"{name}.exe" if os.name == "nt" else name
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "ffmpeg" / executable  # type: ignore[attr-defined]
        if bundled.exists():
            return str(bundled)
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} was not found. Install FFmpeg or rebuild the app with bundled tools.")
    return found


def probe_video(path: Path) -> VideoInfo:
    command = [
        find_tool("ffprobe"),
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type",
        "-of",
        "json",
        str(path),
    ]
    result = _run(command)
    payload = json.loads(result.stdout)
    duration = float(payload["format"]["duration"])
    has_audio = any(stream.get("codec_type") == "audio" for stream in payload.get("streams", []))
    return VideoInfo(path=path, duration=duration, has_audio=has_audio)


def sample_frames(video: VideoInfo, destination: Path, interval: float) -> list[tuple[Path, float]]:
    destination.mkdir(parents=True, exist_ok=True)
    pattern = destination / "frame_%08d.jpg"
    _run(
        [
            find_tool("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video.path),
            "-vf",
            f"fps=1/{interval}",
            "-q:v",
            "3",
            str(pattern),
        ]
    )
    frames = sorted(destination.glob("frame_*.jpg"))
    return [(frame, index * interval) for index, frame in enumerate(frames)]


def extract_clip(video: VideoInfo, start: float, end: float, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    duration = end - start
    video_filter = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30"
    command = [
        find_tool("ffmpeg"),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(video.path),
    ]
    if video.has_audio:
        command.extend(["-map", "0:v:0", "-map", "0:a:0"])
    else:
        command.extend(
            [
                "-f",
                "lavfi",
                "-t",
                f"{duration:.3f}",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
            ]
        )
    command.extend(
        [
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            "-shortest",
            str(destination),
        ]
    )
    _run(command)


def concatenate_clips(clips: list[Path], destination: Path, list_file: Path) -> None:
    list_file.write_text(
        "".join(f"file '{str(clip.resolve()).replace(chr(39), chr(39) * 3)}'\n" for clip in clips),
        encoding="utf-8",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            find_tool("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    )


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed: {Path(command[0]).name}\n{detail}")
    return result