# Auto Video Stitch

Auto Video Stitch is a Windows desktop tool that finds scenes matching a written description, a reference image, or both across one or more video files. It records each source file and timestamp, extracts the matching ranges, and stitches them into an MP4 at a location you choose.

The processing flow reuses the approach demonstrated by `DrummerHighlightGenerator`: FFmpeg/FFprobe inventory and sampling, scored frame detections, timestamp merging and padding, normalized clip extraction, concatenation, and CSV/JSON result artifacts. Scene detection is generalized from a fixed YOLO person target to OpenAI CLIP semantic image-text similarity. The referenced `video_edit_manta` directory contained no source files.

## Use the app

1. Open `dist\AutoVideoStitch\AutoVideoStitch.exe`.
2. Add one or more videos.
3. Describe the scene, choose a reference image for visual or facial-likeness matching, or provide both.
4. Choose the result MP4 path and select **Find and stitch scenes**.

The app writes three files in the chosen folder:

- The stitched `.mp4` video.
- A `_scenes.csv` file containing source paths, start/end seconds, and similarity scores.
- A `_summary.json` file containing the query and the same machine-readable scene details.

On first use, the app downloads the `openai/clip-vit-base-patch32` model from Hugging Face (about 600 MB) into the current user's model cache. Videos and sampled frames remain local. Later runs use the cached model.

## Search settings

- **Sample every** controls search precision and speed. Lower values inspect more frames.
- **Match threshold** controls strictness. Typical values are `0.20` to `0.30` for text and `0.70` to `0.90` for a reference image. Choosing an image changes the untouched default to `0.75`.
- **Merge gap** joins nearby matching samples into one scene.
- **Clip padding** adds context before and after each match.

Reference matching uses whole-image CLIP similarity. For better facial-likeness results, use a clear, tightly cropped, front-facing photo and lower the sample interval. This is visual similarity, not biometric identity verification, and should not be used for identity, security, employment, or other consequential decisions.

## Build on Windows

Prerequisites are Python 3.11+ and FFmpeg/FFprobe on `PATH`.

```powershell
.\build.ps1
```

The distributable folder is `dist\AutoVideoStitch`. Keep the complete folder together because the executable, Python libraries, and bundled FFmpeg tools are all required.

## Develop and test

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m autovideostitch
```