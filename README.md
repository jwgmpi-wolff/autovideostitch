# AutoVideoStitch

A Windows video stitching app with local AI scene filtering and a command-line planning
interface.

<!-- project-downloads:start -->
## APK and installer downloads

| Package | Download | Source |
| --- | --- | --- |
| Windows installer | [AutoVideoStitch-Setup-1.0.4.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.4/AutoVideoStitch-Setup-1.0.4.exe) | v1.0.4 |
| Windows executable | [AutoVideoStitch.exe](https://media.githubusercontent.com/media/jwgmpi-wolff/autovideostitch/main/dist/AutoVideoStitch.exe) | Git LFS package |

Android may require approval to install apps from this download source. Debug APKs are labeled above. Windows executables that are not setup packages may require accompanying project files; follow the project-specific instructions below.

- [Download the complete source ZIP](https://github.com/jwgmpi-wolff/autovideostitch/archive/refs/heads/main.zip).
<!-- project-downloads:end -->

## Desktop app

Run the installed command without clip arguments:

```console
autovideostitch
```

The desktop app can add, remove, clear, and reorder clips, select an output path, choose
face, reference-image, or text-description AI scene filtering, and render the matching
scenes into an MP4. The dedicated `autovideostitch-gui` command opens the same
interface.

Face filtering uses a bundled OpenCV detector. Reference-image and text-description
filtering use the local CLIP model. CLIP weights are downloaded from Hugging Face on
first use and cached for subsequent runs.

Scene selection ranks sampled frames across all input videos and retains only the
strongest confident matches. Face mode scores detected face size and count, reference
image mode scores visual similarity, and text descriptions use semantic CLIP scores.
Descriptions mentioning people, faces, portraits, or crowds also incorporate detected
face confidence.

Rendering is performed in a single FFmpeg pass to avoid storing a separate temporary
video for every matched scene. The app checks free space on the output drive before
encoding and reports a clear error when more space is required.

## Windows downloads

Download the production Windows installer and portable distribution from the
[AutoVideoStitch v1.0.4 GitHub release](https://github.com/jwgmpi-wolff/autovideostitch/releases/tag/v1.0.4).
The release also includes SHA256 checksums for verifying the downloads.

## Command line

Pass one or more clips to use the command-line interface:

```console
autovideostitch first.mp4 second.mp4 --output stitched_output.mp4
```

Use the same AI filters from the command line:

```console
autovideostitch first.mp4 --scene-filter face --output faces.mp4
autovideostitch first.mp4 --scene-filter image --filter-value person.jpg --output matches.mp4
autovideostitch first.mp4 --scene-filter text --filter-value "a person riding a bicycle" --output bicycle.mp4
```

## Copyright

Copyright (c) 2026 Jerry Wolff. See [COPYRIGHT](COPYRIGHT) for the scope of this
notice. Existing licenses and third-party attribution remain unchanged; this
notice does not grant additional permissions.
