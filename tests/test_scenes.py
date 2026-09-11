from pathlib import Path

from autovideostitch.scenes import FrameMatch, SceneMatch, group_frame_matches


def test_groups_nearby_matches_and_clamps_padding() -> None:
    video = Path("input.mp4")

    scenes = group_frame_matches(
        [
            FrameMatch(video, 1.0, 0.72),
            FrameMatch(video, 3.0, 0.81),
            FrameMatch(video, 12.0, 0.75),
        ],
        sample_interval=2.0,
        merge_gap=1.0,
        padding=2.0,
        durations={video: 15.0},
    )

    assert scenes == [
        SceneMatch(video, 0.0, 7.0, 0.81),
        SceneMatch(video, 10.0, 15.0, 0.75),
    ]


def test_keeps_videos_separate() -> None:
    first = Path("first.mp4")
    second = Path("second.mp4")

    scenes = group_frame_matches(
        [FrameMatch(second, 2.0, 0.8), FrameMatch(first, 2.0, 0.9)],
        sample_interval=1.0,
        merge_gap=1.0,
        padding=0.0,
        durations={first: 10.0, second: 10.0},
    )

    assert [scene.video_path for scene in scenes] == [first, second]