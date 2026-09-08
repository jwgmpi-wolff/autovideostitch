# Auto Video Stitch

Auto Video Stitch is a Windows desktop tool that finds scenes matching a written description, a reference image, or both across one or more video files. It records each source file and timestamp, extracts the matching ranges, and stitches them into an MP4 at a location you choose.

The processing flow reuses the approach demonstrated by `DrummerHighlightGenerator`: FFmpeg/FFprobe inventory and sampling, scored frame detections, timestamp merging and padding, normalized clip extraction, concatenation, and CSV/JSON result artifacts. Scene detection is generalized from a fixed YOLO person target to OpenAI CLIP semantic image-text similarity. The referenced `video_edit_manta` directory contained no source files.

## Use the app

Download the current Windows release:

- [Online installer (smaller download)](https://github.com/jwgmpi-wolff/autovideostitch/releases/latest/download/AutoVideoStitch-Online-Setup-1.0.2.exe)
- [Offline installer (includes the scene model)](https://github.com/jwgmpi-wolff/autovideostitch/releases/latest/download/AutoVideoStitch-Setup-1.0.2.exe)
- [Portable Windows app (`.zip`)](https://github.com/jwgmpi-wolff/autovideostitch/releases/latest/download/AutoVideoStitch-Portable-1.0.2.zip)
- [SHA-256 checksums](https://github.com/jwgmpi-wolff/autovideostitch/releases/latest/download/AutoVideoStitch-1.0.2-SHA256.txt)

The repository is private, so GitHub prompts authorized users to sign in before downloading.

1. Install with either setup executable, or extract the complete portable ZIP and open `AutoVideoStitch.exe`.
2. Add one or more videos.
3. Describe the scene, choose a reference image for visual or facial-likeness matching, or provide both.
4. Choose the result MP4 path and select **Find and stitch scenes**.

The app writes three files in the chosen folder:

- The stitched `.mp4` video.
- A `_scenes.csv` file containing source paths, start/end seconds, and similarity scores.
- A `_summary.json` file containing the query and the same machine-readable scene details.

Both installers include FFmpeg, FFprobe, the Python runtime, and all required libraries. The smaller online installer downloads the `openai/clip-vit-base-patch32` scene-recognition model from Hugging Face on the first search and caches it in the user profile; internet access is required for that first download. The offline installer and portable app bundle the model and need no additional downloads. Videos and sampled frames remain local.

## Search settings

- **Sample every** controls search precision and speed. Lower values inspect more frames.
- **Match threshold** controls strictness. Typical values are `0.20` to `0.30` for text and `0.70` to `0.90` for a reference image. Choosing an image changes the untouched default to `0.75`.
- **Merge gap** joins nearby matching samples into one scene.
- **Clip padding** adds context before and after each match.

Reference matching uses whole-image CLIP similarity. For better facial-likeness results, use a clear, tightly cropped, front-facing photo and lower the sample interval. This is visual similarity, not biometric identity verification, and should not be used for identity, security, employment, or other consequential decisions.

## Build on Windows

Build prerequisites are Python 3.11+, FFmpeg/FFprobe on `PATH`, and internet access to download the scene-recognition model into the build output. End users do not need these prerequisites because they are included in the installer and portable app.

```powershell
.\build.ps1
```

The distributable folder is `dist\AutoVideoStitch`. Keep the complete folder together because the executable, Python libraries, and bundled FFmpeg tools are all required.

To create the installer, portable ZIP, and checksums:

```powershell
.\release.ps1
```

To create the smaller installer that downloads the scene model on first use:

```powershell
.\release.ps1 -OnlineInstaller
```

This requires Inno Setup 6 (`winget install JRSoftware.InnoSetup`).

## Develop and test

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m autovideostitch
```