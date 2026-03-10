---
name: md-to-audio
description: Convert a Markdown (.md) file to an MP3 audio file using edge-tts. Use this skill whenever the user says they want to generate audio, TTS, or mp3 from a markdown document, particularly using edge-tts or the Yunxi male voice.
---

# Markdown to Audio (edge-tts)

This skill allows you to convert a local Markdown (`.md`) file into a spoken audio file (`.mp3`) using `edge-tts`.
By default, this workflow uses the "zh-CN-YunxiNeural" (云希男声) voice, but can be customized.

## Prerequisites

If not already available in the user's environment, `edge-tts` is required. You can try installing it:
`pip3 install edge-tts` (or via `brew install pipx` and `pipx install edge-tts`).

## How to execute

A Python script is bundled with this skill to make the conversion easy. It automatically reads the markdown file, calls `edge-tts`, and outputs an `.mp3` file to an `audio` directory in the current working directory.

The script is located at: `scripts/md_to_audio.py`

### Usage

```bash
python3 .agent/skills/md-to-audio/scripts/md_to_audio.py "/absolute/path/to/document.md"
```

### Options

You can specify a custom output directory using `--out-dir` or change the voice via `--voice`.
```bash
python3 .agent/skills/md-to-audio/scripts/md_to_audio.py "document.md" --out-dir "/path/to/custom_audio_dir" --voice "zh-CN-XiaoxiaoNeural"
```

## Post-Execution
- Check the terminal output to ensure that the conversion succeeded without errors.
- Confirm the generated MP3 file path and let the user know where to find the generated audio.
