import sys
import traceback
from pathlib import Path

from autovideostitch.ui import main


def verify_runtime(report_path: Path) -> int:
    try:
        import torch
        from transformers.models.clip.modeling_clip import CLIPModel  # noqa: F401

        report_path.write_text(f"Torch {torch.__version__} loaded successfully.\n", encoding="utf-8")
        return 0
    except BaseException:
        report_path.write_text(traceback.format_exc(), encoding="utf-8")
        return 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-runtime":
        raise SystemExit(verify_runtime(Path(sys.argv[2])))
    main()