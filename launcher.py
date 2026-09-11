import sys

from autovideostitch.cli import main as cli_main
from autovideostitch.gui import main as gui_main


if __name__ == "__main__":
    raise SystemExit(cli_main(sys.argv[1:]) if sys.argv[1:] else gui_main())
