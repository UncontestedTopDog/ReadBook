# 拆书 (ChaiShu) 自动化处理工具集

本项目包含一系列 AI 辅助工作流（Skills），旨在帮助用户自动化处理电子书、长文本内容，并将其流水线式地转换为单人语音朗读、对谈式播客脚本以及完整的多角色播客音频附件。

---

## 已包含的 Skills (流程节点) 概览

1. **epub-to-markdown**: EPUB 提取转 Markdown 工具
2. **md-to-audio**: Markdown 单人文本转语音 (MP3) 工具
3. **md-to-podcast**: Markdown 转多角色对谈式播客脚本生成器
4. **podcast-script-to-audio**: 播客脚本转多角色音频及同步字幕生成器

---

## 详细功能及用法文档

### 1. epub-to-markdown (EPUB 二进制转文本提取器)

- **含义**: 将 `.epub` 格式的电子书无损解析并按原书目录 (nav.xhtml) 拆分成多个独立的 Markdown (`.md`) 文件。作为项目文本处理源头的首要前置工程，适合处理整本电子书以便后续分章节精读或加工转换。
- **用法 (CLI)**:  
  ```bash
  python .agent/skills/epub-to-markdown/scripts/epub_extractor.py <path_to_epub_file> [--output_base <可选的主输出目录>]
  ```
- **输入**: 
  - `<path_to_epub_file>`: (必填) 用户提供的 `.epub` 原始文件路径。
- **参数**: 
  - `--output_base`: (选填) 提取出的各章节内容的存放主目录。默认值为 `chapters`。在该目录下，脚本会自动基于输入的 EPUB 文件名生成对应的子文件夹集，所有的核心 `.md` 文件将存放在内。

---

### 2. md-to-audio (文本转有声书/单人朗读)

- **含义**: 利用微软云语音合成服务 `edge-tts`，将本地生成的章节的 Markdown 文件高品质转换为单人朗读的 MP3 音频文件，并同时生成便于校对或前端带高亮播放演示的 `.vtt` 同步格式字幕文件。
- **用法 (CLI)**:  
  ```bash
  python3 .agent/skills/md-to-audio/scripts/md_to_audio.py <markdown文档路径> [--out-dir <音频输出目录>] [--voice <声线配音员名称>]
  ```
- **输入**: 
  - `<markdown文档路径>`: (必填) `.md` 源文件的绝对或相对路径。
- **参数**: 
  - `--out-dir`: (选填) 自定义音频的输出文件夹，默认会在当前目录下创建存放 `audio`。
  - `--voice`: (选填) 选择发音人 TTS 声学模型。默认值为口语流利沉稳的自然音色 `"zh-CN-YunxiNeural"`（云希），也可替换为如 `"zh-CN-XiaoxiaoNeural"`（晓晓）等。

*(注: 该脚本会自动将产物一分为二，分别为 `<原名>_Audio.mp3` 以及单独存放在 `subtitles` 目录的 `<原名>_Subtitles.vtt`)*

---

### 3. md-to-podcast (播客脚本 AI 生成工作流)

- **含义**: 基于大语言模型进行重构。将生硬的长篇文章或章节 Markdown 文档转换为具有**多沉浸发声角色（Host A 与 Host B 等）**的自然对谈播客脚本 (`.md`)。该过程严格保证内容忠实性，强制包含原文所有的核心逻辑锚点而杜绝核心信息的丢失。
- **用法**: 
  主要依赖自然语言对话或大模型 Agent Workflow 进行直接触发执行。
- **输入**:
  - 提供源头解析好的分章节纯文本 Markdown 文件。
- **参数/规范**: 
  - **角色设计**: 建立一个兼具知识渊博者与现代生活代入感的组合架构（“老司机”与“小白”经典配置），并加入如背景乐渐入 `*(BGM：轻松治愈的吉他曲渐入)*` 这样的演出级音频舞台提示词。
  - **内容输出**: 完整保留要点体系（比如原文有 17 点核心知识，剧本就一定保留并演绎完成 17 段对话）。在对应的并列结构目录（例如 `script/对应的书名/xx_Script.md`）落文件。

---

### 4. podcast-script-to-audio (播客脚本转最终拼合音频)

- **含义**: 基于生成的对话剧本，串联解析角色标识与文本，将多角色的播客文案渲染成最终带有独立播音音色混排的完整 `.mp3` 播客成品音频及伴生多角色 `.vtt` 字幕。
- **用法 (CLI)**:  
  ```bash
  python3 .agent/skills/podcast-script-to-audio/scripts/generate_podcast.py <生成的对谈脚本路径> [--out-dir <音频输出目录>] [--sub-dir <字幕输出目录>]
  ```
- **输入**: 
  - `<生成的对谈脚本路径>`: (必填) 符合标识语法的包含角色粗体标记的 Markdown 剧本文件（例如，带有类似 `**主播A**：今天...` 格式的文本）。
- **参数**: 
  - `--out-dir`: (选填) 指定合成合并后播客音频文件的输出主目录。默认为 `podcast/<父级分类>/<剧本名>_Podcast.mp3`。
  - `--sub-dir`: (选填) 指定对应的多音轨文字合并 VTT 字幕输出目录。默认为 `podcast_subtitles/<父级分类>/<剧本名>_Podcast.vtt`。

- **工作机制**: 该脚本可自动匹配和注册 Markdown 中的每一位角标（自动寻找如 `**姓名**:`），通过 `edge-tts` 调用给每个演员临时生成对白切片，随后借助 `ffmpeg` 将所有长短句无缝平滑拼接，用完即丢短切片而留存完成包与精准字幕时间对齐。

---

## 环境与核心依赖声明

系统需要前置安装以下必须核心库来支持所有的媒体与转换功能运作：

```bash
# 安装最新的 TTS 引擎支持
pip install edge-tts

# 必须的环境系统变量 (用于终极音频混合拼接裁切)
# 在 macOS 下的安装方法：
brew install ffmpeg
```
