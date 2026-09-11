import pytest

from autovideostitch import (
    SceneFilter,
    __version__,
    stitch_clips,
    validate_clip_list,
    validate_scene_filter,
)
from autovideostitch.cli import build_parser, main


def test_version_is_set():
    assert __version__


def test_validate_clip_list_accepts_values():
    assert validate_clip_list(["clip1.mp4", "clip2.mp4"]) == ["clip1.mp4", "clip2.mp4"]


def test_stitch_clips_appends_output_path():
    assert stitch_clips(["clip1.mp4", "clip2.mp4"], output_path="merged.mp4") == [
        "clip1.mp4",
        "clip2.mp4",
        "merged.mp4",
    ]


def test_parser_allows_no_clips_for_desktop_app():
    assert build_parser().parse_args([]).clips == []


def test_cli_renders_when_clips_are_provided(capsys, monkeypatch):
    monkeypatch.setattr(
        "autovideostitch.cli.render_video",
        lambda clips, output, scene_filter: output,
    )
    assert main(["clip1.mp4", "clip2.mp4", "--output", "merged.mp4"]) == 0
    assert capsys.readouterr().out.strip() == "merged.mp4"


def test_face_scene_filter_is_supported():
    assert validate_scene_filter("face") == SceneFilter(mode="face")


def test_text_scene_filter_requires_a_description():
    with pytest.raises(ValueError, match="text description"):
        validate_scene_filter("text", " ")

    assert validate_scene_filter("text", "  a person riding a bicycle  ") == SceneFilter(
        mode="text",
        value="a person riding a bicycle",
    )


def test_image_scene_filter_requires_an_existing_image(tmp_path):
    image = tmp_path / "reference.jpg"
    image.write_bytes(b"image")
    assert validate_scene_filter("image", str(image)) == SceneFilter(
        mode="image",
        value=str(image),
    )

    with pytest.raises(ValueError, match="does not exist"):
        validate_scene_filter("image", str(tmp_path / "missing.jpg"))
