from __future__ import annotations

import csv
import json
from pathlib import Path

from .scenes import SceneMatch


def write_reports(
    scenes: list[SceneMatch],
    description: str,
    output_video: Path,
    reference_image: Path | None = None,
) -> tuple[Path, Path]:
    csv_path = output_video.with_name(f"{output_video.stem}_scenes.csv")
    json_path = output_video.with_name(f"{output_video.stem}_summary.json")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["file", "start_seconds", "end_seconds", "score"])
        writer.writeheader()
        for scene in scenes:
            writer.writerow(
                {
                    "file": str(scene.video_path),
                    "start_seconds": f"{scene.start:.3f}",
                    "end_seconds": f"{scene.end:.3f}",
                    "score": f"{scene.score:.4f}",
                }
            )
    json_path.write_text(
        json.dumps(
            {
                "description": description,
                "reference_image": str(reference_image) if reference_image else None,
                "output_video": str(output_video),
                "scene_count": len(scenes),
                "scenes": [
                    {
                        "file": str(scene.video_path),
                        "start_seconds": scene.start,
                        "end_seconds": scene.end,
                        "score": scene.score,
                    }
                    for scene in scenes
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return csv_path, json_path