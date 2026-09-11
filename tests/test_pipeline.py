import pytest
from types import SimpleNamespace

from autovideostitch.pipeline import (
    VideoProcessingError,
    VideoSegment,
    _build_filter_graph,
    _description_requests_people,
    _ensure_free_space,
    _merge_times,
    _score_threshold,
    render_video,
)


def test_merge_times_combines_overlapping_samples():
    assert _merge_times("clip.mp4", [1.0, 2.0, 6.0], 10.0, 1.0, 0.5) == [
        VideoSegment("clip.mp4", 0.5, 3.5),
        VideoSegment("clip.mp4", 5.5, 7.5),
    ]


def test_merge_times_clamps_ranges_to_video_duration():
    assert _merge_times("clip.mp4", [0.0, 9.5], 10.0, 1.0, 1.0) == [
        VideoSegment("clip.mp4", 0.0, 2.0),
        VideoSegment("clip.mp4", 8.5, 10.0),
    ]


def test_merge_times_returns_no_segments_without_matches():
    assert _merge_times("clip.mp4", [], 10.0, 1.0, 0.5) == []


def test_render_video_rejects_an_empty_output_path():
    with pytest.raises(ValueError, match="output path"):
        render_video(["clip.mp4"], " ")


def test_filter_graph_handles_clips_with_and_without_audio():
    segments = [
        VideoSegment("one.mp4", 1.0, 2.5),
        VideoSegment("two.mp4", 0.0, 1.0),
    ]
    graph = _build_filter_graph(
        segments,
        {"one.mp4": 0, "two.mp4": 1},
        {"one.mp4": True, "two.mp4": False},
    )
    assert "[0:a:0]atrim=start=1.000000:end=2.500000" in graph
    assert "anullsrc=r=48000:cl=stereo,atrim=duration=1.000000" in graph
    assert "concat=n=2:v=1:a=1[outv][outa]" in graph


def test_free_space_preflight_explains_destination_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "autovideostitch.pipeline.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=1),
    )
    with pytest.raises(VideoProcessingError, match="Choose an output folder"):
        _ensure_free_space(
            tmp_path / "output.mp4",
            [VideoSegment("clip.mp4", 0.0, 10.0)],
        )


def test_score_threshold_keeps_only_strong_description_matches():
    scores = [0.231, 0.234, 0.236, 0.269, 0.271]
    threshold = _score_threshold(scores, "text")
    assert threshold > scores[2]
    assert [score for score in scores if score >= threshold] == [0.269, 0.271]


def test_score_threshold_rejects_low_confidence_results():
    with pytest.raises(VideoProcessingError, match="confidently matched"):
        _score_threshold([0.12, 0.18, 0.19], "text")


def test_people_descriptions_enable_face_scoring():
    assert _description_requests_people("a woman speaking to a crowd")
    assert _description_requests_people("close-up portrait")
    assert not _description_requests_people("a red sports car")
