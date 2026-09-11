import ctypes
import os
import sys
from pathlib import Path


if sys.platform == "win32" and getattr(sys, "frozen", False):
    runtime_root = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    dll_directories = (runtime_root, runtime_root / "torch" / "lib")
    dll_directory_handles = []
    for dll_directory in dll_directories:
        if dll_directory.is_dir():
            dll_directory_handles.append(os.add_dll_directory(str(dll_directory)))

    for runtime_name in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
        runtime_path = runtime_root / runtime_name
        if runtime_path.is_file():
            ctypes.WinDLL(str(runtime_path))