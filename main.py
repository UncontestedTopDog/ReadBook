import os
import sys
import shutil
import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Add the epub_extractor path
script_dir = os.path.dirname(os.path.abspath(__file__))
extractor_path = os.path.join(script_dir, '.agent', 'skills', 'epub-to-markdown', 'scripts')
sys.path.append(extractor_path)

audio_script_dir = os.path.join(script_dir, '.agent', 'skills', 'md-to-audio', 'scripts')
sys.path.append(audio_script_dir)

podcast_script_dir = os.path.join(script_dir, '.agent', 'skills', 'podcast-script-to-audio', 'scripts')
sys.path.append(podcast_script_dir)

from epub_extractor import extract_chapters
from md_to_audio import convert_md_to_audio
from generate_podcast import generate_podcast

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

os.makedirs("audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

os.makedirs("podcast", exist_ok=True)
app.mount("/podcast", StaticFiles(directory="podcast"), name="podcast")

os.makedirs("subtitles", exist_ok=True)
app.mount("/subtitles", StaticFiles(directory="subtitles"), name="subtitles")

os.makedirs("podcast_subtitles", exist_ok=True)
app.mount("/podcast_subtitles", StaticFiles(directory="podcast_subtitles"), name="podcast_subtitles")

os.makedirs("mindmap", exist_ok=True)
app.mount("/mindmap", StaticFiles(directory="mindmap"), name="mindmap")

def read_book_details(book_name):
    base_chapters_dir = os.path.join(script_dir, "chapters")
    book_dir = os.path.join(base_chapters_dir, book_name)
    
    if not os.path.exists(book_dir):
        return None
        
    # Load custom order if exists
    order_path = os.path.join(book_dir, "order.json")
    custom_order = []
    if os.path.exists(order_path):
        try:
            with open(order_path, "r", encoding="utf-8") as f:
                custom_order = json.load(f)
        except:
            pass

    raw_chapters = {}
    cover_base64 = None
    
    for filename in os.listdir(book_dir):
        filepath = os.path.join(book_dir, filename)
        if filename.startswith("cover."):
            with open(filepath, "rb") as f:
                ext = os.path.splitext(filename)[1].lower()
                mime_type = f"image/{ext[1:]}" if ext in [".png", ".jpg", ".jpeg", ".webp"] else "image/jpeg"
                encoded = base64.b64encode(f.read()).decode('utf-8')
                cover_base64 = f"data:{mime_type};base64,{encoded}"
        elif filename.endswith(".md"):
            chapter_title = filename.replace(".md", "")
            
            # 检查音频是否已生成
            audio_path = os.path.join(script_dir, "audio", book_name, f"{chapter_title}_Audio.mp3")
            has_audio = os.path.exists(audio_path)
            
            # 检查播客是否已生成
            podcast_path = os.path.join(script_dir, "podcast", book_name, f"{chapter_title}_Script_Podcast.mp3")
            has_podcast = os.path.exists(podcast_path)
            
            podcast_script_content = None
            if has_podcast:
                script_path = os.path.join(script_dir, "script", book_name, f"{chapter_title}_Script.md")
                if os.path.exists(script_path):
                    with open(script_path, "r", encoding="utf-8") as sf:
                        podcast_script_content = sf.read()
                        
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                raw_chapters[chapter_title] = {
                    "title": chapter_title,
                    "content": content,
                    "podcast_content": podcast_script_content,
                    "has_audio": has_audio,
                    "has_podcast": has_podcast
                }
    
    # Apply custom order or default sorted
    chapters = []
    if custom_order:
        for title in custom_order:
            if title in raw_chapters:
                chapters.append(raw_chapters.pop(title))
    
    # Add remaining chapters sorted by name
    remaining_titles = sorted(raw_chapters.keys())
    for title in remaining_titles:
        chapters.append(raw_chapters[title])
                
    # 检查思维导图是否已生成
    mindmap_dir = os.path.join(script_dir, "mindmap", book_name)
    mindmap_path = os.path.join(mindmap_dir, f"{book_name}_MindMap.md")
    
    # 兼容旧路径检查 (如果旧路径存在且新路径不存在，则自动迁移)
    old_mindmap_path = os.path.join(book_dir, "mindmap.md")
    if os.path.exists(old_mindmap_path) and not os.path.exists(mindmap_path):
        os.makedirs(mindmap_dir, exist_ok=True)
        shutil.move(old_mindmap_path, mindmap_path)

    has_mindmap = os.path.exists(mindmap_path)
    mindmap_content = None
    if has_mindmap:
        with open(mindmap_path, "r", encoding="utf-8") as f:
            mindmap_content = f.read()

    return {
        "book_name": book_name,
        "cover": cover_base64,
        "chapters": chapters,
        "has_mindmap": has_mindmap,
        "mindmap": mindmap_content
    }

@app.post("/api/upload")
def upload_epub(file: UploadFile = File(...)):
    try:
        book_name = os.path.splitext(file.filename)[0]
        
        # 保存原始 EPUB 文件到本地 original 目录
        original_dir = os.path.join(script_dir, "original")
        os.makedirs(original_dir, exist_ok=True)
        epub_path = os.path.join(original_dir, file.filename)
        
        with open(epub_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 提取 EPUB 到本地 chapters 目录
        base_chapters_dir = os.path.join(script_dir, "chapters")
        output_dir = os.path.join(base_chapters_dir, book_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # 调用技能提取
        extract_chapters(epub_path, output_dir)
        
        # 读取返回提取的内容
        details = read_book_details(book_name)
        if details:
            return JSONResponse({"success": True, **details})
        else:
            return JSONResponse({"success": False, "error": "Extraction failed or chapter directory missing"})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/books")
async def get_books():
    base_chapters_dir = os.path.join(script_dir, "chapters")
    if not os.path.exists(base_chapters_dir):
        return JSONResponse({"books": []})
    
    books = []
    # 跳过隐藏文件夹等
    for book_name in sorted(os.listdir(base_chapters_dir)):
        if book_name.startswith('.'):
            continue
        book_dir = os.path.join(base_chapters_dir, book_name)
        if os.path.isdir(book_dir):
            cover_base64 = None
            chapter_count = 0
            for filename in os.listdir(book_dir):
                if filename.startswith("cover."):
                    filepath = os.path.join(book_dir, filename)
                    with open(filepath, "rb") as f:
                        ext = os.path.splitext(filename)[1].lower()
                        mime_type = f"image/{ext[1:]}" if ext in [".png", ".jpg", ".jpeg", ".webp"] else "image/jpeg"
                        encoded = base64.b64encode(f.read()).decode('utf-8')
                        cover_base64 = f"data:{mime_type};base64,{encoded}"
                elif filename.endswith(".md"):
                    chapter_count += 1
            books.append({
                "name": book_name,
                "cover": cover_base64,
                "chapter_count": chapter_count
            })
    return JSONResponse({"books": books})

@app.get("/api/books/{book_name}")
async def get_book(book_name: str):
    details = read_book_details(book_name)
    if details:
        return JSONResponse({"success": True, **details})
    else:
        return JSONResponse({"success": False, "error": "Book not found"})

class OrderRequest(BaseModel):
    book_name: str
    order: list[str]

@app.post("/api/books/{book_name}/order")
async def save_book_order(book_name: str, req: OrderRequest):
    try:
        base_chapters_dir = os.path.join(script_dir, "chapters")
        book_dir = os.path.join(base_chapters_dir, book_name)
        if not os.path.exists(book_dir):
            return JSONResponse({"success": False, "error": "Book not found"}, status_code=404)
        
        order_path = os.path.join(book_dir, "order.json")
        with open(order_path, "w", encoding="utf-8") as f:
            json.dump(req.order, f, ensure_ascii=False, indent=2)
            
        return JSONResponse({"success": True, "message": "排序已保存"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

class AudioRequest(BaseModel):
    book_name: str
    chapter_title: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    api_base_url: Optional[str] = None
    force_recreate: Optional[bool] = False

@app.post("/api/generate_audio")
def generate_chapter_audio(req: AudioRequest):
    try:
        base_chapters_dir = os.path.join(script_dir, "chapters")
        book_dir = os.path.join(base_chapters_dir, req.book_name)
        md_file_path = os.path.join(book_dir, f"{req.chapter_title}.md")
        
        if not os.path.exists(md_file_path):
            return JSONResponse({"success": False, "error": "Markdown file not found"}, status_code=404)
        
        # 调用技能进行音频转换和VTT提取
        convert_md_to_audio(md_file_path, subtitles=True)
        return JSONResponse({"success": True, "message": "音频及字幕生成成功"})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/generate_mindmap")
def generate_book_mindmap(req: AudioRequest):
    try:
        base_chapters_dir = os.path.join(script_dir, "chapters")
        book_dir = os.path.join(base_chapters_dir, req.book_name)
        mindmap_dir = os.path.join(script_dir, "mindmap", req.book_name)
        os.makedirs(mindmap_dir, exist_ok=True)
        mindmap_path = os.path.join(mindmap_dir, f"{req.book_name}_MindMap.md")
        
        # 借助 AI 生成全书思维导图 (Mermaid 格式)
        api_key = req.api_key or os.getenv("OPENAI_API_KEY")
        api_base_url = req.api_base_url or os.getenv("OPENAI_API_BASE")
        
        if not api_key or api_key == "在这里填入你的API_KEY":
            return JSONResponse({
                "success": False, 
                "error": "未配置 API_KEY！\n请在网页顶部的「⚙️ 设置模型」中填入你的 API KEY。"
            }, status_code=400)
            
        # 读取所有章节标题和前几行作为摘要
        context_parts = []
        for filename in sorted(os.listdir(book_dir)):
            if filename.endswith(".md") and filename != "mindmap.md":
                with open(os.path.join(book_dir, filename), "r", encoding="utf-8") as f:
                    content = f.read()
                    context_parts.append(f"章节: {filename.replace('.md', '')}\n内容摘要: {content[:500]}...")
        
        source_context = "\n\n".join(context_parts)

        prompt = f"""
请根据以下书籍章节内容摘要，生成一个精炼的书籍思维导图。
要求：
1. 使用标准 Markdown 语法（使用 # 表示核心主题，## 表示章节/主要模块，### 表示子点，- 表示具体细节）。
2. 结构要严谨且丰富，涵盖书中的核心逻辑、关键方法论和独特见解。
3. 请只输出 Markdown 内容即可，不要包含 ```markdown 这种代码块包装，也不要任何解释。

书籍名称：{req.book_name}
内容如下：
{source_context}
"""
        model_name = req.model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client_kwargs = {"api_key": api_key}
        if api_base_url:
            client_kwargs["base_url"] = api_base_url
        client = OpenAI(**client_kwargs)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个擅长提炼书籍精华和制作思维导图的专家。"},
                {"role": "user", "content": prompt}
            ]
        )
        mindmap_content = response.choices[0].message.content
        
        with open(mindmap_path, "w", encoding="utf-8") as f:
            f.write(mindmap_content)
            
        return JSONResponse({"success": True, "mindmap": mindmap_content})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/generate_podcast")
def generate_chapter_podcast(req: AudioRequest):
    try:
        base_chapters_dir = os.path.join(script_dir, "chapters")
        base_script_dir = os.path.join(script_dir, "script")
        book_script_dir = os.path.join(base_script_dir, req.book_name)
        os.makedirs(book_script_dir, exist_ok=True)
        md_script_path = os.path.join(book_script_dir, f"{req.chapter_title}_Script.md")
        
        # 如果强行重新生成，就先删掉之前的脚本文件
        if req.force_recreate and os.path.exists(md_script_path):
            os.remove(md_script_path)
        
        # Output directories
        out_audio_dir = os.path.join(script_dir, "podcast")
        out_sub_dir = os.path.join(script_dir, "podcast_subtitles")
        
        if req.force_recreate:
            # 清理旧的音频和字幕文件
            old_audio = os.path.join(out_audio_dir, req.book_name, f"{req.chapter_title}_Script_Podcast.mp3")
            if os.path.exists(old_audio):
                os.remove(old_audio)
        
        if not os.path.exists(md_script_path):
            # 自动借助 OpenAI 或其他兼容接口进行生成 (优先读取请求参数，其次使用环境变量)
            api_key = req.api_key or os.getenv("OPENAI_API_KEY")
            api_base_url = req.api_base_url or os.getenv("OPENAI_API_BASE")
            
            if not api_key or api_key == "在这里填入你的API_KEY":
                return JSONResponse({
                    "success": False, 
                    "error": "未配置 API_KEY！\n请在网页顶部的「⚙️ 设置模型」中填入你的 API KEY。"
                }, status_code=400)
            
            # 读取原始提取出来的 MD 章节文稿
            md_file_path = os.path.join(base_chapters_dir, req.book_name, f"{req.chapter_title}.md")
            if not os.path.exists(md_file_path):
                return JSONResponse({"success": False, "error": "源文稿缺失，无法提取大纲。"}, status_code=404)
                
            with open(md_file_path, "r", encoding="utf-8") as f:
                source_content = f.read()

            prompt = f"""
请将以下文本内容转换为结构化的双人播客对谈脚本。
**角色设定**：
* **星辰**：知识渊博的引导者。带领主题、引入原句概念。
* **漫步**：幽默接地气的搭档。代表现代听众，反应真实，喜欢用现代日常举例子。

**要求**：
1. 请不要总结跳过，将原文的所有核心点按顺序讲解，写出一个生动自然的口语化对谈。保留原文的精华和细节。
2. 对话结构需包含：开篇（Hooks）、正文（分点解析）、尾声（总结和行动指南）。
3. 必须使用以下精确的格式去标记讲话者（加粗人名后跟全角冒号，不要加引号）：
**星辰**：xxxx
**漫步**：y y y y...
4. 剧本必须全直接对话，除了讲话人以外不需要舞台提示音，纯文字对话。

以下是正文阅读材料：
{source_content}
"""         
            try:
                model_name = req.model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                print(f"📡 正在联机 {model_name} 进行 AI 重写： {req.chapter_title}...")
                
                # 初始化 OpenAI 客户端
                client_kwargs = {"api_key": api_key}
                if api_base_url:
                    client_kwargs["base_url"] = api_base_url
                client = OpenAI(**client_kwargs)
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "你是一个专业的播客脚本撰稿人。请严格按照要求将文本转换为双人播客对白。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                script_content = response.choices[0].message.content
                
                # 持久化报错脚本文档
                with open(md_script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                print(f"✅ 生成对白脚本成功: {md_script_path}")
            except Exception as e:
                return JSONResponse({"success": False, "error": f"调用大模型时出错: {str(e)}"}, status_code=500)

        # 调用技能进行多人播客生成
        generate_podcast(md_script_path, out_audio_dir, out_sub_dir)
        return JSONResponse({"success": True, "message": "Podcast及字幕生成成功"})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/ai_sort")
async def ai_smart_sort(req: AudioRequest):
    try:
        base_chapters_dir = os.path.join(script_dir, "chapters")
        book_dir = os.path.join(base_chapters_dir, req.book_name)
        if not os.path.exists(book_dir):
            return JSONResponse({"success": False, "error": "Book not found"}, status_code=404)
        
        # 获取所有待排序的章节标题
        chapter_titles = []
        for filename in os.listdir(book_dir):
            if filename.endswith(".md") and filename != "mindmap.md":
                chapter_titles.append(filename.replace(".md", ""))
        
        if not chapter_titles:
            return JSONResponse({"success": False, "error": "No chapters found"}, status_code=404)

        # 调 AI 进行逻辑排序
        api_key = req.api_key or os.getenv("OPENAI_API_KEY")
        api_base_url = req.api_base_url or os.getenv("OPENAI_API_BASE")
        
        if not api_key or api_key == "在这里填入你的API_KEY":
            return JSONResponse({
                "success": False, 
                "error": "未配置 API_KEY！\n请在网页顶部的「⚙️ 设置模型」中填入你的 API KEY。"
            }, status_code=400)

        prompt = f"""
你是一个专业的书籍编辑。请根据以下书籍《{req.book_name}》的章节标题，结合内容逻辑（如：开篇、论据、结论、或时间线），给出一个最合理的阅读排序。

待排序章节列表：
{json.dumps(chapter_titles, ensure_ascii=False)}

要求：
1. 请直接返回一个 JSON 数组，包含所有原始章节名称。
2. 不要输出任何解释说明文字。
3. 确保包含列表中的每一个章节，不要遗漏。
"""
        model_name = req.model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client_kwargs = {"api_key": api_key}
        if api_base_url:
            client_kwargs["base_url"] = api_base_url
        client = OpenAI(**client_kwargs)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个书籍内容排版专家。请只返回 JSON 数组格式的结果。"},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" } if "gpt-4" in model_name or "gpt-3.5" in model_name else None
        )
        
        content = response.choices[0].message.content.strip()
        # 尝试解析 JSON。有的模型可能会返回 {"order": [...]} 或直接 [...]
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "order" in data:
                sorted_titles = data["order"]
            elif isinstance(data, list):
                sorted_titles = data
            elif isinstance(data, dict):
                # 寻找第一个列表类型的 key
                sorted_titles = next((v for v in data.values() if isinstance(v, list)), chapter_titles)
            else:
                sorted_titles = chapter_titles
        except:
            # 兜底：如果解析失败，尝试提取数组部分
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                sorted_titles = json.loads(match.group())
            else:
                sorted_titles = chapter_titles

        return JSONResponse({"success": True, "order": sorted_titles})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/test_connection")
async def test_connection(req: AudioRequest):
    try:
        api_key = req.api_key
        api_base_url = req.api_base_url
        model_name = req.model_name or "gpt-4o-mini"
        
        if not api_key:
            return JSONResponse({"success": False, "error": "API Key is required"}, status_code=400)
            
        client_kwargs = {"api_key": api_key, "timeout": 10.0}
        if api_base_url:
            client_kwargs["base_url"] = api_base_url
            
        client = OpenAI(**client_kwargs)
        
        # Perform a minimal test call
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5
        )
        
        return JSONResponse({"success": True, "message": "Connection successful!"})
    except Exception as e:
        error_msg = str(e)
        # Simplify common error messages
        if "401" in error_msg:
            error_msg = "Invalid API Key (401)"
        elif "404" in error_msg:
            error_msg = f"Model '{model_name}' not found or invalid Base URL (404)"
        return JSONResponse({"success": False, "error": error_msg}, status_code=200)

@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.get("/book.html")
def read_book_html():
    from fastapi.responses import FileResponse
    return FileResponse("static/book.html")

@app.get("/chapter.html")
def read_chapter_html():
    from fastapi.responses import FileResponse
    return FileResponse("static/chapter.html")

