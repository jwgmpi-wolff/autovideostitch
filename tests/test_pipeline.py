import json
from pathlib import Path

from autovideostitch.pipeline import SearchOptions, run_search
from autovideostitch.video import VideoInfo


class FakeMatcher:
    def __init__(self, _progress: object) -> None:
        pass

    def score(
        self, _description: str, images: list[Path], _reference_image: Path | None = None
    ) -> list[float]:
        return [0.4 if image.stem.endswith(("1", "2")) else 0.1 for image in images]


def test_search_creates_ordered_clips_and_reports(monkeypatch: object, tmp_path: Path) -> None:
    from autovideostitch import pipeline

    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    output = tmp_path / "results" / "found.mp4"
    extracted: list[tuple[Path, float, float]] = []

    monkeypatch.setattr(pipeline, "SemanticMatcher", FakeMatcher)  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "probe_video", lambda path: VideoInfo(path, 20.0, True))  # type: ignore[attr-defined]

    def fake_samples(video: VideoInfo, destination: Path, _interval: float) -> list[tuple[Path, float]]:
        return [(destination / f"frame_{index}.jpg", float(index * 2)) for index in range(3)]

    def fake_extract(video: VideoInfo, start: float, end: float, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.touch()
        extracted.append((video.path, start, end))

    def fake_concat(_clips: list[Path], destination: Path, _list_file: Path) -> None:
        destination.touch()

    monkeypatch.setattr(pipeline, "sample_frames", fake_samples)  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "extract_clip", fake_extract)  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "concatenate_clips", fake_concat)  # type: ignore[attr-defined]

    scenes = run_search(
        [first, second],
        "a person at a drum kit",
        output,
        SearchOptions(sample_interval=2.0, threshold=0.3, merge_gap=0.0, padding=1.0),
    )

    assert output.exists()
    assert [item[0] for item in extracted] == [first, second]
    assert [(scene.start, scene.end) for scene in scenes] == [(1.0, 7.0), (1.0, 7.0)]
    report = json.loads((output.parent / "found_summary.json").read_text(encoding="utf-8"))
    assert report["description"] == "a person at a drum kit"
    assert report["reference_image"] is None
    assert report["scene_count"] == 2


def test_reference_image_can_replace_text(monkeypatch: object, tmp_path: Path) -> None:
    from autovideostitch import pipeline

    video = tmp_path / "video.mp4"
    reference = tmp_path / "person.jpg"
    reference.touch()
    output = tmp_path / "result.mp4"

    class ReferenceMatcher(FakeMatcher):
        def score(self, description: str, images: list[Path], reference_image: Path | None = None) -> list[float]:
            assert description == ""
            assert reference_image == reference
            return [0.9]

    monkeypatch.setattr(pipeline, "SemanticMatcher", ReferenceMatcher)  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "probe_video", lambda path: VideoInfo(path, 5.0, False))  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "sample_frames", lambda *_args: [(tmp_path / "frame.jpg", 1.0)])  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "extract_clip", lambda *_args: None)  # type: ignore[attr-defined]
    monkeypatch.setattr(pipeline, "concatenate_clips", lambda _clips, destination, _list: destination.touch())  # type: ignore[attr-defined]

    scenes = run_search([video], "", output, SearchOptions(threshold=0.5), reference_image=reference)

    assert len(scenes) == 1
    report = json.loads((tmp_path / "result_summary.json").read_text(encoding="utf-8"))
    assert report["reference_image"] == str(reference)