---
name: html-color-extractor
description: Extracts color values (Hex, RGB, RGBA) from an HTML file and finds matching color names from a reference Swift file (BTColor.swift). Outputs a JSON mapping of colors to names (existing or new) in the same directory as the HTML file.
---

# HTML Color Extractor

## Overview

This skill extracts all color values defined in an HTML file (including inline styles, embedded CSS, and Tailwind config scripts), matches them against a reference Swift file containing color definitions, and outputs a JSON file mapping each unique color found to a name.

- **Existing Colors:** If a color found in the HTML matches a value in the Swift file, the existing Swift variable name is used.
- **New Colors:** If no match is found, a new name is generated (e.g., `color_HEXVALUE`).

## Workflow

1.  **Dependencies**: Requires Python 3.
2.  **Input**:
    -   `html_path`: Absolute path to the HTML file.
    -   `swift_path`: Absolute path to the reference Swift file (defaults to `AudioBook/BrainTraining/Utils/BTColor.swift`).
3.  **Process**:
    -   Parses the Swift file to build a lookup table of `{HexValue: ColorName}`.
        -   Supports `Color(hex: "...")` and `dynamicColor(light: "...", dark: "...")`.
    -   Parses the HTML file to find all occurrences of colors:
        -   Hex codes (3, 4, 6, 8 digits).
        -   RGB/RGBA functions (converted to Hex for matching).
    -   Normalizes all colors to Hex format (6 or 8 digits, uppercase).
    -   Matches normalized colors against the Swift lookup table.
    -   Generates a JSON map:
        ```json
        {
          "colors": [
            {
              "hex": "#FF0000",
              "name": "brandPrimary",
              "is_existing": true
            },
            {
              "hex": "#123456",
              "name": "color_123456",
              "is_existing": false
            }
          ]
        }
        ```
    -   Saves the JSON file as `{html_filename}_colors.json` in the same directory as the HTML file.

## Usage

```bash
python3 /Users/lizhi/WillsIdea/BrainTraining/.agent/skills/html-color-extractor/scripts/extract_colors.py \
  --html-path "/path/to/file.html" \
  --swift-path "/Users/lizhi/WillsIdea/BrainTraining/AudioBook/BrainTraining/Utils/BTColor.swift"
```

## Example

**User:** "Extract colors from @[stitch_downloads/Tech Mastery Ranks v1.html]"

**Agent:**
1.  Identify the HTML file path.
2.  Run the python script.
3.  Output: "Colors extracted to `stitch_downloads/Tech Mastery Ranks v1_colors.json`."
