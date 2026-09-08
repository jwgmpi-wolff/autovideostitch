from pathlib import Path

import pytest

from autovideostitch import semantic


def test_model_source_uses_bundled_model_when_frozen(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    bundled = tmp_path / semantic.BUNDLED_MODEL_PATH
    bundled.mkdir(parents=True)
    monkeypatch.setattr(semantic.sys, "frozen", True, raising=False)
    monkeypatch.setattr(semantic.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert semantic.model_source() == (bundled, True)


def test_model_source_rejects_missing_bundled_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(semantic.sys, "frozen", True, raising=False)
    monkeypatch.setattr(semantic.sys, "_MEIPASS", str(tmp_path), raising=False)

    with pytest.raises(RuntimeError, match="installed scene recognition model is missing"):
        semantic.model_source()


def test_model_source_allows_download_for_online_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / semantic.ONLINE_MODEL_MARKER).touch()
    monkeypatch.setattr(semantic.sys, "frozen", True, raising=False)
    monkeypatch.setattr(semantic.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert semantic.model_source() == (semantic.MODEL_ID, False)