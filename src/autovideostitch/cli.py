"""Command line entry point for AutoVideoStitch."""

from __future__ import annotations

import argparse
from typing import Sequence

from .core import validate_scene_filter
from .pipeline import VideoProcessingError, render_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AutoVideoStitch")
    parser.add_argument(
        "clips",
        nargs="*",
        help="Input video clips to stitch. Omit clips to open the desktop app.",
    )
    parser.add_argument("-o", "--output", default="stitched_output.mp4", help="Output file path")
    parser.add_argument(
        "--scene-filter",
        choices=("none", "face", "image", "text"),
        default="none",
        help="Only include scenes matching this filter",
    )
    parser.add_argument(
        "--filter-value",
        default="",
        help="Reference image path or text description for the selected filter",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.clips:
        from .gui import main as gui_main

        return gui_main()

    try:
        scene_filter = validate_scene_filter(args.scene_filter, args.filter_value)
        output = render_video(args.clips, args.output, scene_filter)
    except (ValueError, VideoProcessingError) as exc:
        parser.error(str(exc))

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
