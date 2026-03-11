---
name: md-to-podcast
description: Convert a Markdown text (article or book chapter) into a comprehensive, multi-character conversational podcast script, preserving all core points in distinct sections.
---

# md-to-podcast

This skill guides the agent in generating a high-quality, comprehensive podcast dialogue script from a Markdown document. It ensures that the generated script is engaging, conversational, and retains all the core information from the original text by dedicating a section to each main point.

## Trigger 
Use this skill when the user asks to generate an audio script, podcast script, conversational script (e.g., 播客脚本, 音频对谈脚本, 音频博客) from a text or markdown file, particularly when they emphasize retaining details or covering every core point.

## Instructions

When the user asks you to generate a podcast script from a document, follow these exact steps:

### Step 1: Analyze the Source Material
1. Thoroughly read the provided Markdown file.
2. Identify all the distinct logical sections, numbered points, or core ideas in the text. For example, if the text has 17 sections, you must identify all 17. 
3. **Do not summarize or skip points** unless the user explicitly tells you to cut content. The user expects *all* core points to be preserved.

### Step 2: Establish Format and Roles
Create a natural, engaging two-person conversational format.
1. **Host A (The Guide)**: Intellectual, calm, and knowledgeable. This host leads the topic, introduces original quotes/concepts, and sets the structure.
2. **Host B (The Relatable Co-host)**: Humorous, grounded, represents the "modern listener" (e.g., an office worker). This host reacts to Host A, raises common pain points, and translates deep or ancient concepts into everyday modern examples.
3. **Audio Cues**: Include BGM and sound effect cues in the script (e.g., `*(BGM：轻松治愈的吉他曲渐入)*`) to give it a produced feel.

### Step 3: Draft the Script
Write the script in a highly spoken, natural tone (口语化). 
1. **Intro**: Casual greeting, introduce the topic, and raise a modern hook or pain point that connects to the theme.
2. **Body (Section by Section)**: Create a distinct dialogue segment for **EVERY individual core point** you identified in Step 1. 
   - Label each section clearly (e.g., `## 🎧 第X点：[主题]`).
   - For each point, Host A introduces the theory/story, and Host B reacts or connects it to modern life.
3. **Outro**: Summarize the takeaways, provide actionable practical steps (if mentioned in the text), and sign off smoothly.

### Step 4: Output
Save the complete dialogue script into a new Markdown file using the `write_to_file` tool. The output filename must be the original Markdown filename appended with `_Script` (e.g., `OriginalFileName_Script.md`). The file should be saved in a `script` directory that is at the same level as the `chapters` directory, preserving the rest of the subfolder structure (e.g., if the input is `/path/to/chapters/topic/chapter1.md`, the output should be `/path/to/script/topic/chapter1_Script.md`). Create any necessarily directories if they do not exist. Make sure to use proper Markdown formatting with bolding for speakers and italic/bold for audio cues.

## Example Output Structure
```markdown
# 🎧 [Title] 音频对谈脚本

**角色设定**：
* **[Host A Name]**：...
* **[Host B Name]**：...

---

## 🎙️ 开篇：[Hook Topic]
*(BGM: ...)*
**[Host A Name]**：大家好...
**[Host B Name]**：今天我们要聊...

## 🎧 第一点：[Core Point 1]
**[Host A Name]**：书中讲到...
**[Host B Name]**：这不就是我们现在说的...

... (Repeat for ALL points)

## 🎧 尾声：[Summary]
**[Host A Name]**：感谢收听...
**[Host B Name]**：下期见！
```
