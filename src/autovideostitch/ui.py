from __future__ import annotations

import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .pipeline import SearchOptions, run_search
from .video import VIDEO_EXTENSIONS


class AutoVideoStitchApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Auto Video Stitch")
        self.geometry("820x710")
        self.minsize(700, 640)
        self.video_paths: list[Path] = []
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.output_path = tk.StringVar(value=str(Path.home() / "Videos" / "scene_results.mp4"))
        self.reference_image = tk.StringVar()
        self.sample_interval = tk.StringVar(value="2.0")
        self.threshold = tk.StringVar(value="0.24")
        self.merge_gap = tk.StringVar(value="3.0")
        self.padding = tk.StringVar(value="2.0")
        self.status = tk.StringVar(value="Ready")
        self._build_ui()
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 20))
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 10))
        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Auto Video Stitch", style="Title.TLabel").pack(anchor="w")
        ttk.Label(container, text="Find scenes by description or reference image and assemble them in source order.").pack(
            anchor="w", pady=(2, 20)
        )

        files_header = ttk.Frame(container)
        files_header.pack(fill="x")
        ttk.Label(files_header, text="VIDEO FILES", style="Section.TLabel").pack(side="left")
        ttk.Button(files_header, text="Add videos", command=self._add_videos).pack(side="right")
        ttk.Button(files_header, text="Remove", command=self._remove_videos).pack(side="right", padx=8)
        self.file_list = tk.Listbox(container, height=7, selectmode="extended")
        self.file_list.pack(fill="x", pady=(6, 18))

        ttk.Label(container, text="SCENE DESCRIPTION", style="Section.TLabel").pack(anchor="w")
        self.description = tk.Text(container, height=4, wrap="word", font=("Segoe UI", 10))
        self.description.pack(fill="x", pady=(6, 12))

        ttk.Label(container, text="REFERENCE IMAGE (OPTIONAL)", style="Section.TLabel").pack(anchor="w")
        image_row = ttk.Frame(container)
        image_row.pack(fill="x", pady=(6, 18))
        ttk.Entry(image_row, textvariable=self.reference_image, state="readonly").pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(image_row, text="Choose image", command=self._choose_reference_image).pack(
            side="right", padx=(8, 0)
        )
        ttk.Button(image_row, text="Clear", command=self._clear_reference_image).pack(
            side="right", padx=(8, 0)
        )

        ttk.Label(container, text="RESULT VIDEO", style="Section.TLabel").pack(anchor="w")
        output_row = ttk.Frame(container)
        output_row.pack(fill="x", pady=(6, 14))
        ttk.Entry(output_row, textvariable=self.output_path).pack(side="left", fill="x", expand=True)
        ttk.Button(output_row, text="Browse", command=self._choose_output).pack(side="right", padx=(8, 0))

        settings = ttk.LabelFrame(container, text="Search settings", padding=12)
        settings.pack(fill="x", pady=(0, 18))
        fields = [
            ("Sample every (seconds)", self.sample_interval),
            ("Match threshold", self.threshold),
            ("Merge gap (seconds)", self.merge_gap),
            ("Clip padding (seconds)", self.padding),
        ]
        for column, (label, variable) in enumerate(fields):
            ttk.Label(settings, text=label).grid(row=0, column=column, sticky="w", padx=(0, 8))
            ttk.Entry(settings, textvariable=variable, width=15).grid(row=1, column=column, sticky="ew", padx=(0, 8))
            settings.columnconfigure(column, weight=1)

        self.progress = ttk.Progressbar(container, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        status_row = ttk.Frame(container)
        status_row.pack(fill="x", pady=(6, 0))
        ttk.Label(status_row, textvariable=self.status).pack(side="left")
        self.open_button = ttk.Button(status_row, text="Open result folder", command=self._open_result_folder, state="disabled")
        self.open_button.pack(side="right")
        self.run_button = ttk.Button(status_row, text="Find and stitch scenes", command=self._start)
        self.run_button.pack(side="right", padx=8)

    def _add_videos(self) -> None:
        patterns = " ".join(f"*{extension}" for extension in sorted(VIDEO_EXTENSIONS))
        selected = filedialog.askopenfilenames(title="Select video files", filetypes=[("Video files", patterns), ("All files", "*.*")])
        for value in selected:
            path = Path(value)
            if path not in self.video_paths:
                self.video_paths.append(path)
                self.file_list.insert("end", str(path))

    def _remove_videos(self) -> None:
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
            del self.video_paths[index]

    def _choose_output(self) -> None:
        selected = filedialog.asksaveasfilename(
            title="Save result video",
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")],
            initialfile=Path(self.output_path.get()).name,
        )
        if selected:
            self.output_path.set(selected)

    def _choose_reference_image(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select a reference image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")],
        )
        if selected:
            self.reference_image.set(selected)
            if self.threshold.get() == "0.24":
                self.threshold.set("0.75")

    def _clear_reference_image(self) -> None:
        self.reference_image.set("")
        if self.threshold.get() == "0.75":
            self.threshold.set("0.24")

    def _start(self) -> None:
        try:
            options = SearchOptions(
                sample_interval=float(self.sample_interval.get()),
                threshold=float(self.threshold.get()),
                merge_gap=float(self.merge_gap.get()),
                padding=float(self.padding.get()),
            )
        except ValueError:
            messagebox.showerror("Invalid settings", "Search settings must contain valid numbers.")
            return
        description = self.description.get("1.0", "end").strip()
        reference_image = Path(self.reference_image.get()) if self.reference_image.get() else None
        output = Path(self.output_path.get()).expanduser()
        self.run_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.progress.configure(value=0)
        worker = threading.Thread(
            target=self._run_worker,
            args=(list(self.video_paths), description, reference_image, output, options),
            daemon=True,
        )
        worker.start()

    def _run_worker(
        self,
        videos: list[Path],
        description: str,
        reference_image: Path | None,
        output: Path,
        options: SearchOptions,
    ) -> None:
        try:
            scenes = run_search(
                videos,
                description,
                output,
                options,
                lambda message, fraction: self.events.put(("progress", (message, fraction))),
                reference_image,
            )
            self.events.put(("complete", (output.with_suffix(".mp4"), len(scenes))))
        except Exception as error:
            self.events.put(("error", str(error)))

    def _drain_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "progress":
                    message, fraction = payload  # type: ignore[misc]
                    self.status.set(str(message))
                    self.progress.configure(value=float(fraction) * 100)
                elif event == "complete":
                    output, count = payload  # type: ignore[misc]
                    self.status.set(f"Found {count} scenes. Saved {output}")
                    self.progress.configure(value=100)
                    self.run_button.configure(state="normal")
                    self.open_button.configure(state="normal")
                    messagebox.showinfo("Complete", f"Found {count} scenes and created:\n{output}")
                elif event == "error":
                    self.status.set("Search failed")
                    self.run_button.configure(state="normal")
                    messagebox.showerror("Auto Video Stitch", str(payload))
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _open_result_folder(self) -> None:
        folder = Path(self.output_path.get()).expanduser().parent
        if os.name == "nt":
            os.startfile(folder)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(folder)])


def main() -> None:
    AutoVideoStitchApp().mainloop()