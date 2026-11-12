---
description: Peak-normalize audio files to -1 dB with ffmpeg
argument-hint: "<input folder> <output folder> [peak dB, default -1]"
---

Peak-normalize every audio file in an input folder into an output folder with FFmpeg. Arguments from `$ARGUMENTS`: input folder, output folder, optional target peak in dB (default `-1`). Ask for any folder that is missing.

1. List the audio files (`.wav`, `.mp3`, `.ogg`, `.flac`) in the input folder. Stop if there are none.
2. Create the output folder and `<input folder>/completed` if missing.
3. For each file:
   - **Detect the peak:** `ffmpeg -hide_banner -i "<in>/<file>" -af volumedetect -f null - 2>&1 | grep max_volume`
   - **Gain** = target peak minus `max_volume`. Example: target -1, max -13.9 gives +12.9 dB.
   - **Apply:** `ffmpeg -hide_banner -i "<in>/<file>" -af "volume=<gain>dB" -y "<out>/<file>"`
   - **Move** the source into `<input folder>/completed/` only after the output file exists.
4. Report each file with its gain, and any errors.
