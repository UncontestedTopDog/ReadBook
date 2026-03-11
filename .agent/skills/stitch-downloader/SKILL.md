---
name: stitch-downloader
description: |
  Automatically triggered when user sends a Stitch URL (https://stitch.withgoogle.com/projects/...) with no special instructions.
  Downloads PNG and HTML from the design, then generates frontend web code that 100% recreates the UI.
---

# Stitch Downloader

## Overview

This skill allows you to download the screenshot (PNG) and the associated code (HTML) of a design from a Stitch project URL, then generate frontend web code (HTML/CSS/JS or framework like React) that 100% recreates the UI design. It automatically names the files based on the design title, appending numbers if duplicates exist.

## Trigger Conditions

**自动触发此技能的条件：**
- 用户发送的消息包含 Stitch URL（格式：`https://stitch.withgoogle.com/projects/...`）
- 用户没有其他特殊说明或指令

**示例触发消息：**
- `https://stitch.withgoogle.com/projects/12007425047885203739?node-id=5a6e7fbd1fc348ae80a0b58894b63877`
- `这个设计 https://stitch.withgoogle.com/projects/...`

**不触发的情况：**
- 用户明确说「只下载」或「不要生成代码」
- 用户有其他特定需求描述

## Workflow

### Phase 1: Download Assets

1.  **Parse the Stitch URL**
    Extract the `project_id` and `screen_id` (also known as `node_id`) from the provided URL.
    -   Standard URL format: `https://stitch.withgoogle.com/projects/{project_id}?node-id={screen_id}`
    -   Example: `https://stitch.withgoogle.com/projects/12007425047885203739?node-id=5a6e7fbd1fc348ae80a0b58894b63877`
    -   `project_id`: `12007425047885203739`
    -   `screen_id`: `5a6e7fbd1fc348ae80a0b58894b63877`

2.  **Get Screen Details**
    Call the `mcp_stitch_get_screen` tool with the extracted IDs.
    -   `projectId`: The extracted `project_id`
    -   `screenId`: The extracted `screen_id`

3.  **Download and Rename Assets**
    The `get_screen` response will contain:
    -   `title`: The name of the design.
    -   `screenshot.downloadUrl`: URL for the PNG.
    -   `htmlCode.downloadUrl`: URL for the HTML.

    Run the provided python script to download and name the files correctly.
    
    ```bash
    python3 /Users/lizhi/WillsIdea/Skills/.agent/skills/stitch-downloader/scripts/download_stitch_assets.py \
      --title "{title_from_response}" \
      --png-url "{screenshot_url}" \
      --html-url "{html_url}" \
      --output-dir "stitch_downloads"
    ```

    *Note: Ensure to quote the arguments to handle spaces in the title or URL.*

4.  **Confirm Download**
    Notify the user that the files have been successfully downloaded and provide their filenames.

### Phase 2: Generate Frontend Web Code

5.  **Analyze the Design**
    Use the downloaded PNG and HTML files as UI references:
    -   **PNG file**: Visual reference for layout, colors, spacing, and overall appearance
    -   **HTML file**: Code reference for exact color values, font sizes, dimensions, and structure

6.  **Extract Design Specifications from HTML**
    Parse the HTML file to extract:
    -   Color values (hex, RGB, RGBA)
    -   Font sizes and font families
    -   Dimensions (width, height, padding, margin)
    -   Border radius values
    -   Shadow specifications
    -   Layout structure (flexbox, positioning)

7.  **Confirm File Naming with User**
    Before generating the web code, ask the user to confirm the file name:
    -   Provide a recommended name based on the design title (e.g., `{title}.tsx` or `{title}.html`)
    -   Convert title to PascalCase for components or kebab-case for pure HTML
    -   Example: "Login Page" → `LoginPage.tsx` or `login-page.html`
    -   Wait for user confirmation or alternative name

8.  **Generate Frontend Web Code**
    Create frontend web code that 100% recreates the UI:
    -   Match all colors exactly using exact hex or RGB values in CSS
    -   Match all dimensions, padding, and spacing precisely
    -   Use appropriate HTML semantic tags and CSS layout (Flexbox/Grid)
    -   Implement proper CSS styling properties (width, height, padding, border-radius, etc.)
    -   Add necessary custom components or CSS classes for complex parts
    -   Ensure code can be easily viewed in a standard web browser

9.  **Code Quality Checklist**
    Ensure the generated code:
    -   [ ] Uses exact colors from the HTML/design
    -   [ ] Matches exact dimensions and spacing
    -   [ ] Has proper font sizes and weights
    -   [ ] Implements correct corner radius values
    -   [ ] Includes shadows if present in design
    -   [ ] Uses proper layout structure (Flexbox/Grid)
    -   [ ] Is well-commented and organized
    -   [ ] Is responsive and testable in a browser

## Example

**User:** "Download and implement: https://stitch.withgoogle.com/projects/12007425047885203739?node-id=5a6e7fbd1fc348ae80a0b58894b63877"

**Agent:**
1.  Calls `mcp_stitch_get_screen` → returns `title="Login Page"`.
2.  Runs:
    ```bash
    python3 /Users/lizhi/WillsIdea/Skills/.agent/skills/stitch-downloader/scripts/download_stitch_assets.py \
      --title "Login Page" \
      --png-url "https://..." \
      --html-url "https://..." \
      --output-dir "stitch_downloads"
    ```
3.  Output: "Successfully downloaded: stitch_downloads/Login Page.png and Login Page.html"
4.  Views both files to analyze the design.
5.  Extracts colors, dimensions, and layout from HTML.
6.  Asks user: "我已下载完成设计稿。推荐的文件名为 `LoginPage.tsx` 或 `login-page.html`，请确认或提供其他名称。"
7.  User confirms: "好的，就用这个名字"
8.  Generates frontend web code and saves to the confirmed filename.
9.  Responds: "已生成代码，100% 还原了 UI 设计。"

## Notes

- Always use the HTML file as the source of truth for exact values (colors, sizes, etc.)
- Use the PNG file to verify visual accuracy and understand the overall layout
- When in doubt about a value, prefer the HTML specification over visual estimation
- Generate clean, maintainable frontend web code (HTML/CSS/JS or framework specific) following modern web best practices
