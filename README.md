# AutoVideoStitch

A Windows video stitching app with local AI scene filtering and a command-line planning
interface.

<!-- project-downloads:start -->
## APK and installer downloads

Every available project package is indexed below, including older versions. Prefer the newest stable version for your platform and architecture. Debug APKs and prereleases are labeled; archives are not necessarily standalone installers.

### Release downloads: all published versions

| Version / source | Package | Download |
| --- | --- | --- |
| v1.0.4 | Portable distribution archive | [AutoVideoStitch-Portable-1.0.4.zip](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.4/AutoVideoStitch-Portable-1.0.4.zip) |
| v1.0.4 | Windows installer | [AutoVideoStitch-Setup-1.0.4.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.4/AutoVideoStitch-Setup-1.0.4.exe) |
| v1.0.3 | Windows installer | [AutoVideoStitch-Online-Setup-1.0.3.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.3/AutoVideoStitch-Online-Setup-1.0.3.exe) |
| v1.0.3 | Portable distribution archive | [AutoVideoStitch-Portable-1.0.3.zip](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.3/AutoVideoStitch-Portable-1.0.3.zip) |
| v1.0.3 | Windows installer | [AutoVideoStitch-Setup-1.0.3.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.3/AutoVideoStitch-Setup-1.0.3.exe) |
| v1.0.2 | Windows installer | [AutoVideoStitch-Online-Setup-1.0.2.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.2/AutoVideoStitch-Online-Setup-1.0.2.exe) |
| v1.0.2 | Portable distribution archive | [AutoVideoStitch-Portable-1.0.2.zip](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.2/AutoVideoStitch-Portable-1.0.2.zip) |
| v1.0.2 | Windows installer | [AutoVideoStitch-Setup-1.0.2.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.2/AutoVideoStitch-Setup-1.0.2.exe) |
| v1.0.1 | Portable distribution archive | [AutoVideoStitch-Portable-1.0.1.zip](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.1/AutoVideoStitch-Portable-1.0.1.zip) |
| v1.0.1 | Windows installer | [AutoVideoStitch-Setup-1.0.1.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.1/AutoVideoStitch-Setup-1.0.1.exe) |
| v1.0.0 | Portable distribution archive | [AutoVideoStitch-Portable-1.0.0.zip](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.0/AutoVideoStitch-Portable-1.0.0.zip) |
| v1.0.0 | Windows installer | [AutoVideoStitch-Setup-1.0.0.exe](https://github.com/jwgmpi-wolff/autovideostitch/releases/download/v1.0.0/AutoVideoStitch-Setup-1.0.0.exe) |

### Repository-hosted packages: all available versions

| Version / source | Package | Download |
| --- | --- | --- |
| Git LFS | Windows executable | [dist/AutoVideoStitch.exe](https://media.githubusercontent.com/media/jwgmpi-wolff/autovideostitch/main/dist/AutoVideoStitch.exe) |
| Git LFS | Windows executable | [dist/AutoVideoStitch/AutoVideoStitch.exe](https://media.githubusercontent.com/media/jwgmpi-wolff/autovideostitch/main/dist/AutoVideoStitch/AutoVideoStitch.exe) |
| Git LFS | Portable distribution archive | [release/AutoVideoStitch-Portable-1.0.4.zip](https://media.githubusercontent.com/media/jwgmpi-wolff/autovideostitch/main/release/AutoVideoStitch-Portable-1.0.4.zip) |
| Git LFS | Windows installer | [release/AutoVideoStitch-Setup-1.0.4.exe](https://media.githubusercontent.com/media/jwgmpi-wolff/autovideostitch/main/release/AutoVideoStitch-Setup-1.0.4.exe) |

Git LFS links download the package itself, not a pointer file. Executables without a setup wrapper may require accompanying project files.

### Setup scripts and source


- [Download the complete source ZIP](https://github.com/jwgmpi-wolff/autovideostitch/archive/refs/heads/main.zip). Extract the complete checkout before running setup scripts unless the project instructions explicitly support standalone installation.
- [Browse all releases and their assets](https://github.com/jwgmpi-wolff/autovideostitch/releases).

Android may require approval to install apps from the download source. Follow the project-specific installation, signing, checksum, and prerequisite instructions elsewhere in this README.
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
