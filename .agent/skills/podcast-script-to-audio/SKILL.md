---
name: podcast-script-to-audio
description: Convert a generated multi-character Markdown text dialogue script into a final concatenated Podcast mp3 audio file with accompanying VTT subtitles. Use this skill when the user wants to generate podcast audio from a script.
---

# podcast-script-to-audio

This skill allows you to convert a multi-character conversational text script (usually a Markdown file) into a full `.mp3` podcast audio and `.vtt` subtitles file using `edge-tts` and `ffmpeg`.

## How to execute

A Python script is bundled with this skill to make the conversion easy. It automatically reads the markdown script, parses out the speakers by looking for bolded names with colons (e.g., `**星辰**：`), automatically assigns different voices for different speakers, generates temporary audio snippets using `edge-tts`, concatenates them using `ffmpeg`, generates time-synced VTT subtitles, and cleans up after itself.

The script is located at: `scripts/generate_podcast.py`

### Usage

```bash
python3 .agent/skills/podcast-script-to-audio/scripts/generate_podcast.py "/absolute/path/to/script.md"
```

### Options

You can specify a custom output directory for both the audio and the subtitles:
```bash
python3 .agent/skills/podcast-script-to-audio/scripts/generate_podcast.py "script.md" --out-dir "custom_podcast_folder" --sub-dir "custom_subtitles_folder"
```

By default:
- Audio output is routed to `podcast/<category>/<script_name>_Podcast.mp3`
- Subtitles output is routed to `podcast_subtitles/<category>/<script_name>_Podcast.vtt`

## Post-Execution
- Check the terminal output to ensure that the conversion succeeded without errors.
- Confirm the generated MP3 file path and let the user know where to find the generated podcast audio and the subtitles.
