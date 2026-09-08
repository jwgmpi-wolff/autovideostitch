import os
import subprocess

from autovideostitch import video


def test_run_suppresses_process_window_on_windows(monkeypatch: object) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        captured.update(options)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(video.subprocess, "run", fake_run)  # type: ignore[attr-defined]

    video._run(["ffmpeg", "-version"])

    expected = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    assert captured["creationflags"] == expected