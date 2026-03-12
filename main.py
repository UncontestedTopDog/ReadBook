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

def read_book_details(book_name):
    base_chapters_dir = os.path.join(script_dir, "chapters")
    book_dir = os.path.join(base_chapters_dir, book_name)
    
    if not os.path.exists(book_dir):
        return None
        
    chapters = []
    cover_base64 = None
    
    for filename in sorted(os.listdir(book_dir)):
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
                chapters.append({
                    "title": chapter_title,
                    "content": content,
                    "podcast_content": podcast_script_content,
                    "has_audio": has_audio,
                    "has_podcast": has_podcast
                })
                
    return {
        "book_name": book_name,
        "cover": cover_base64,
        "chapters": chapters
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

class AudioRequest(BaseModel):
    book_name: str
    chapter_title: str
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
        return JSONResponse({"success": True, "message": "音频及字母生成成功"})
        
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

