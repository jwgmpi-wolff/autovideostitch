# AutoVideoStitch

A Windows video stitching app with local AI scene filtering and a command-line planning
interface.

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
