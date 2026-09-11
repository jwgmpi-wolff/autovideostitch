import sys
from pathlib import Path

from autovideostitch.cli import main as cli_main
from autovideostitch.gui import main as gui_main


def _verify_runtime(report_path: str) -> int:
    report = Path(report_path)
    try:
        import torch

        torch.zeros(1)
        report.write_text(f"torch={torch.__version__}\n", encoding="utf-8")
    except Exception as exc:
        report.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if arguments and arguments[0] == "--verify-runtime":
        if len(arguments) != 2 or not arguments[1].strip():
            raise SystemExit("usage: --verify-runtime REPORT_PATH")
        raise SystemExit(_verify_runtime(arguments[1]))
    raise SystemExit(cli_main(arguments) if arguments else gui_main())
