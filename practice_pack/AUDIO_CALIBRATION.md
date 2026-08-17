# Audio Pace Calibration

The default **1.0×** MP3 speed is calibrated against the downloadable NAATI Cantonese CCL practice recordings. Those recordings are old CCL materials supplied by NAATI for preparation; they are **not redistributed** in this repository.

## Measured reference pace

Across six downloadable Cantonese practice recordings, source-speech timing was measured separately from the chime and inter-segment silence. The published PDF word counts were used for English; English translation word counts were used as an equivalent-length measure for Cantonese.

- English: approximately **160 words per minute** overall.
- Cantonese: approximately **179 English-equivalent words per minute** overall.
- Real speakers naturally vary by segment, syntax and pause pattern.

## Practice audio target

The independent synthetic MP3 generator targets that average pace at **1.0×**. Mock Exam mode locks playback to 1.0×. Training modes offer slower/faster playback. Browser speech synthesis is only a fallback and its pace depends on the device and installed voice.

## Important limitation

Matching the average pace of downloadable practice recordings does **not** mean a live CCL recording will use one fixed speaking rate. The calibration is for realistic practice difficulty, not a guarantee about future test audio.
