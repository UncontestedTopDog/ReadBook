---
name: epub-to-markdown
description: Extract an EPUB file into separate Markdown chapters. Trigger this skill whenever the user wants to convert, extract, read, or split an EPUB file into text or markdown files.
---

# EPUB to Markdown Extractor

This skill extracts the contents of an EPUB file into separate Markdown (`.md`) files, one for each chapter. It preserves the book's structure based on its internal navigation table (nav.xhtml).

## Components

- **SKILL.md**: The primary instructions for using this skill.
- **scripts/epub_extractor.py**: The Python script responsible for analyzing and extracting the contents of an `.epub` file into separate markdown documents.

## How to use

When a user asks you to extract, convert, or split an EPUB file, execute the built-in python extraction script over the target file.

Run the script by referencing the `epub_extractor.py` relative to the current skill path context:

```bash
python .agent/skills/epub-to-markdown/scripts/epub_extractor.py <path_to_epub_file> [--output_base <optional_base_dir>]
```

- `<path_to_epub_file>`: The absolute or relative path to the `.epub` file provided by the user.
- `--output_base`: (Optional) The base directory where the extracted chapters will be stored. Defaults to `chapters`. Inside this directory, a subfolder with the name of the EPUB file will be created.

### Example Walkthrough

If the user says: "Extract `original/心学日课21天.epub` to markdown"

You should run:
```bash
python .agent/skills/epub-to-markdown/scripts/epub_extractor.py original/心学日课21天.epub
```

This will automatically create a directory structure, e.g. `chapters/心学日课21天/`, and extract the chapters (`第一章 立志.md`, `第二章 格物.md`, etc.), inside it based on the EPUB table of contents.

After extraction, you should verify that the extraction files exist by listing the directory contents and then print a success message to the user.
