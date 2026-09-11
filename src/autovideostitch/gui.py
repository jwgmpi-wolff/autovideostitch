"""Windows desktop interface for AutoVideoStitch."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Sequence

from .core import SceneFilter, validate_scene_filter
from .pipeline import VideoProcessingError, render_video


VIDEO_FILETYPES = [
    ("Video files", "*.mp4 *.mov *.avi *.mkv *.wmv *.m4v"),
    ("All files", "*.*"),
]


class AutoVideoStitchApp:
    """A small native Windows UI for selecting and preparing video clips."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AutoVideoStitch")
        self.root.minsize(760, 620)
        self.root.geometry("880x700")
        self.clip_paths: list[str] = []

        self.output_var = tk.StringVar(value=str(Path.cwd() / "stitched_output.mp4"))
        self.filter_mode_var = tk.StringVar(value="none")
        self.filter_value_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Add video clips to begin.")
        self.worker_events: queue.SimpleQueue[tuple[object, ...]] = queue.SimpleQueue()
        self._build_widgets()
        self.filter_mode_var.trace_add("write", self._update_filter_controls)
        self._update_filter_controls()

    def _build_widgets(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(22, 18, 22, 10))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="AutoVideoStitch", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Combine your video clips in the order shown below.",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        content = ttk.Frame(self.root, padding=(22, 8, 22, 12))
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(content)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="Add videos...", command=self.add_videos).pack(side="left")
        ttk.Button(toolbar, text="Remove selected", command=self.remove_selected).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="Clear list", command=self.clear_list).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="Move up", command=self.move_selected_up).pack(
            side="left", padx=(20, 0)
        )
        ttk.Button(toolbar, text="Move down", command=self.move_selected_down).pack(
            side="left", padx=(8, 0)
        )

        list_frame = ttk.Frame(content)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.clip_list = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            activestyle="none",
            font=("Segoe UI", 10),
            borderwidth=1,
            relief="solid",
        )
        self.clip_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.clip_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.clip_list.configure(yscrollcommand=scrollbar.set)

        scene_filter = ttk.LabelFrame(content, text="AI scene filter", padding=12)
        scene_filter.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        scene_filter.columnconfigure(1, weight=1)
        modes = ttk.Frame(scene_filter)
        modes.grid(row=0, column=0, columnspan=3, sticky="w")
        for text, value in (
            ("All scenes", "none"),
            ("Faces", "face"),
            ("Reference image", "image"),
            ("Text description", "text"),
        ):
            ttk.Radiobutton(
                modes,
                text=text,
                value=value,
                variable=self.filter_mode_var,
            ).pack(side="left", padx=(0, 16))

        self.filter_prompt_label = ttk.Label(scene_filter, text="")
        self.filter_prompt_label.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.filter_value_entry = ttk.Entry(scene_filter, textvariable=self.filter_value_var)
        self.filter_value_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(10, 0))
        self.filter_browse_button = ttk.Button(
            scene_filter,
            text="Browse...",
            command=self.choose_reference_image,
        )
        self.filter_browse_button.grid(row=1, column=2, padx=(8, 0), pady=(10, 0))

        output = ttk.LabelFrame(content, text="Output video", padding=12)
        output.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        output.columnconfigure(0, weight=1)
        ttk.Entry(output, textvariable=self.output_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(output, text="Browse...", command=self.choose_output).grid(
            row=0, column=1, padx=(8, 0)
        )

        footer = ttk.Frame(self.root, padding=(22, 8, 22, 18))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(
            footer,
            variable=self.progress_var,
            maximum=100,
            length=180,
        )
        self.progress_bar.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self.stitch_button = ttk.Button(footer, text="Stitch videos", command=self.stitch)
        self.stitch_button.grid(row=0, column=2, sticky="e", padx=(12, 0))

    def add_videos(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Select video clips",
            filetypes=VIDEO_FILETYPES,
        )
        for path in selected:
            if path not in self.clip_paths:
                self.clip_paths.append(path)
                self.clip_list.insert(tk.END, path)
        self._update_status()

    def remove_selected(self) -> None:
        selected = list(self.clip_list.curselection())
        for index in reversed(selected):
            self.clip_list.delete(index)
            del self.clip_paths[index]
        self._update_status()

    def clear_list(self) -> None:
        self.clip_paths.clear()
        self.clip_list.delete(0, tk.END)
        self._update_status()

    def move_selected_up(self) -> None:
        selected = list(self.clip_list.curselection())
        new_selection = set(selected)
        for index in selected:
            if index == 0 or index - 1 in new_selection:
                continue
            self.clip_paths[index - 1], self.clip_paths[index] = (
                self.clip_paths[index],
                self.clip_paths[index - 1],
            )
            new_selection.remove(index)
            new_selection.add(index - 1)
        self._refresh_clip_list(sorted(new_selection))

    def move_selected_down(self) -> None:
        selected = list(self.clip_list.curselection())
        new_selection = set(selected)
        for index in reversed(selected):
            if index == len(self.clip_paths) - 1 or index + 1 in new_selection:
                continue
            self.clip_paths[index + 1], self.clip_paths[index] = (
                self.clip_paths[index],
                self.clip_paths[index + 1],
            )
            new_selection.remove(index)
            new_selection.add(index + 1)
        self._refresh_clip_list(sorted(new_selection))

    def choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Choose output video",
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4"), ("All files", "*.*")],
            initialfile=Path(self.output_var.get()).name,
        )
        if path:
            self.output_var.set(path)

    def choose_reference_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select reference image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.filter_value_var.set(path)

    def stitch(self) -> None:
        try:
            scene_filter = validate_scene_filter(
                self.filter_mode_var.get(),
                self.filter_value_var.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Cannot stitch videos", str(exc), parent=self.root)
            return

        self.stitch_button.configure(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Starting video processing...")
        worker = threading.Thread(
            target=self._run_stitch,
            args=(tuple(self.clip_paths), self.output_var.get(), scene_filter),
            daemon=True,
        )
        worker.start()
        self.root.after(100, self._poll_worker_events)

    def _run_stitch(
        self,
        clips: Sequence[str],
        output_path: str,
        scene_filter: SceneFilter,
    ) -> None:
        try:
            output = render_video(
                clips,
                output_path,
                scene_filter,
                progress=self._queue_progress,
            )
        except (ValueError, OSError, VideoProcessingError) as exc:
            self.worker_events.put(("error", str(exc)))
            return
        self.worker_events.put(("complete", output, scene_filter))

    def _queue_progress(self, value: float, message: str) -> None:
        self.worker_events.put(("progress", value, message))

    def _poll_worker_events(self) -> None:
        processing = True
        while not self.worker_events.empty():
            event = self.worker_events.get()
            if event[0] == "progress":
                self.progress_var.set(float(event[1]) * 100)
                self.status_var.set(str(event[2]))
            elif event[0] == "error":
                processing = False
                self._stitch_failed(str(event[1]))
            elif event[0] == "complete":
                processing = False
                self._stitch_finished(event[1], event[2])
        if processing:
            self.root.after(100, self._poll_worker_events)

    def _stitch_failed(self, error: str) -> None:
        self.stitch_button.configure(state="normal")
        self.status_var.set("Video processing failed.")
        messagebox.showerror("Cannot stitch videos", error, parent=self.root)

    def _stitch_finished(self, output_path: Path, scene_filter: SceneFilter) -> None:
        self.stitch_button.configure(state="normal")
        self.progress_var.set(100)
        self.status_var.set(f"Created {output_path.name}")
        filter_summary = self._filter_summary(scene_filter)
        messagebox.showinfo(
            "Video complete",
            f"Output:\n{output_path}\n\nScene filter: {filter_summary}",
            parent=self.root,
        )

    def _update_filter_controls(self, *_args: object) -> None:
        mode = self.filter_mode_var.get()
        if mode == "image":
            self.filter_prompt_label.configure(text="Image")
            self.filter_value_entry.configure(state="normal")
            self.filter_browse_button.configure(state="normal")
        elif mode == "text":
            self.filter_prompt_label.configure(text="Describe scenes")
            self.filter_value_entry.configure(state="normal")
            self.filter_browse_button.configure(state="disabled")
        else:
            self.filter_prompt_label.configure(text="")
            self.filter_value_entry.configure(state="disabled")
            self.filter_browse_button.configure(state="disabled")

    @staticmethod
    def _filter_summary(scene_filter: SceneFilter) -> str:
        labels = {
            "none": "All scenes",
            "face": "Faces",
            "image": f"Reference image ({scene_filter.value})",
            "text": f'Text description ("{scene_filter.value}")',
        }
        return labels[scene_filter.mode]

    def _refresh_clip_list(self, selected: Sequence[int]) -> None:
        self.clip_list.delete(0, tk.END)
        for path in self.clip_paths:
            self.clip_list.insert(tk.END, path)
        for index in selected:
            self.clip_list.selection_set(index)
        self._update_status()

    def _update_status(self) -> None:
        count = len(self.clip_paths)
        self.status_var.set(f"{count} clip(s) selected." if count else "Add video clips to begin.")


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    root = tk.Tk()
    AutoVideoStitchApp(root)
    root.mainloop()
    return 0
