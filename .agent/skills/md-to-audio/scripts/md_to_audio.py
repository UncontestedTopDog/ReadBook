import os
import sys
import argparse
import subprocess
from pathlib import Path

def convert_md_to_audio(md_file_path, voice="zh-CN-YunxiNeural", output_dir=None):
    # 将输入路径转为 Path 对象
    md_path = Path(md_file_path).resolve()
    
    # 检查文件是否存在
    if not md_path.exists():
        print(f"❌ 错误：找不到文件 {md_file_path}")
        sys.exit(1)
        
    # 获取文件名（不带扩展名）
    file_name = md_path.stem
    
    # 构建输出路径 (默认在运行路径下的 audio 目录中)
    if output_dir:
        audio_dir = Path(output_dir).resolve()
    else:
        audio_dir = Path.cwd() / "audio"
        
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # 输出音频文件路径
    output_audio_path = audio_dir / f"{file_name}.mp3"
    
    print(f"🎙️  开始转换: {md_path.name}")
    print(f"🗣️  使用声音: {voice}")
    print(f"🗂️  输出路径: {output_audio_path}")
    
    # 构建 edge-tts 命令行调用参数
    command = [
        "edge-tts",
        "--voice", voice,
        "-f", str(md_path),
        "--write-media", str(output_audio_path)
    ]
    
    try:
        # 执行命令 (subprocess 会直接输出 edge-tts 的日志到终端)
        subprocess.run(command, check=True)
        print(f"\n✅ 转换成功！音频文件已保存至: {output_audio_path}")
        return output_audio_path
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 转换失败，错误信息: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ 错误：找不到 'edge-tts' 命令。")
        print("请确保已安装并通过终端可用：运行 `pip3 install edge-tts` (或者使用你本地环境对应的 pip)")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将 Markdown 文件转换为 MP3 音频 (使用 edge-tts)")
    parser.add_argument("md_file", help="要转换的 markdown 文件路径")
    parser.add_argument("--voice", default="zh-CN-YunxiNeural", help="使用的声音，默认：zh-CN-YunxiNeural (云希男声)")
    parser.add_argument("--out-dir", help="自定义输出目录", default=None)
    
    args = parser.parse_args()
    convert_md_to_audio(args.md_file, voice=args.voice, output_dir=args.out_dir)
