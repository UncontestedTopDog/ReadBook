import os
import re
import sys
import argparse
import subprocess
import shutil
from pathlib import Path

def get_audio_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def parse_time(t_str):
    t_str = t_str.replace(",", ".")
    h, m, s = t_str.split(":")
    s, ms = s.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def generate_podcast(md_path, output_dir_base, subtitle_dir_base):
    md_file = Path(md_path)
    output_dir = Path(output_dir_base) / md_file.parent.name
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "temp_segments"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    subtitles_dir = Path(subtitle_dir_base) / md_file.parent.name
    subtitles_dir.mkdir(parents=True, exist_ok=True)

    with open(md_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    snippets = []
    counter = 1
    sub_counter = 1
    
    vtt_lines = ["WEBVTT\n"]
    current_offset = 0.0

    for line in lines:
        line = line.strip()
        # Match lines like "**星辰**：听众朋友们大家好..."
        match = re.match(r"\*\*(.+?)\*\*[：:](.*)", line)
        if match:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            
            if "星辰" in speaker:
                voice = "zh-CN-XiaoxiaoNeural"
            elif "漫步" in speaker:
                voice = "zh-CN-YunxiNeural"
            else:
                voice = "zh-CN-XiaoxiaoNeural" # Fallback
                
            if not text:
                continue
            
            mp3_name = f"{counter:03d}_{speaker}.mp3"
            mp3_path = temp_dir / mp3_name
            sub_path = temp_dir / f"{mp3_name}.vtt"
            
            cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", str(mp3_path), "--write-subtitles", str(sub_path)]
            print(f"Generating {mp3_name} with {voice}...")
            subprocess.run(cmd, check=True)
            
            if sub_path.exists():
                with open(sub_path, "r", encoding="utf-8") as f:
                    sub_content = f.read().strip().split("\n\n")
                    
                for block in sub_content:
                    blines = block.strip().split("\n")
                    if len(blines) >= 3:
                        # Extract timestamps
                        times = blines[1].split(" --> ")
                        if len(times) == 2:
                            start_t = parse_time(times[0]) + current_offset
                            end_t = parse_time(times[1]) + current_offset
                            vtt_lines.append(f"\n{sub_counter}")
                            vtt_lines.append(f"{format_time(start_t)} --> {format_time(end_t)}")
                            vtt_lines.append(f"[{speaker}] " + " ".join(blines[2:]))
                            sub_counter += 1
                            
            current_offset += get_audio_duration(mp3_path)
            
            snippets.append(mp3_path)
            counter += 1

    # Write concat list
    list_file = temp_dir / "file_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for s in snippets:
            f.write(f"file '{s.resolve()}'\n")

    final_audio = output_dir / f"{md_file.stem}_Podcast.mp3"
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(final_audio)
    ]
    print(f"Concatenating {len(snippets)} segments into final audio...")
    subprocess.run(concat_cmd, check=True)
    
    final_vtt = subtitles_dir / f"{md_file.stem}_Podcast.vtt"
    with open(final_vtt, "w", encoding="utf-8") as f:
        f.write("\n".join(vtt_lines) + "\n")

    # Clean up temporary segments
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print("🗑️ Cleaned up temporary segments folder.")

    print(f"\n✅ Podcast successfully generated at: {final_audio}")
    print(f"📝 Subtitles successfully generated at: {final_vtt}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate multi-character podcast audio and VTT from a markdown script.")
    parser.add_argument("script_path", help="Path to the markdown podcast script")
    parser.add_argument("--out-dir", default="podcast", help="Output directory for audio")
    parser.add_argument("--sub-dir", default="podcast_subtitles", help="Output directory for subtitles")
    
    args = parser.parse_args()
    
    if not Path(args.script_path).exists():
        print(f"❌ Error: Script file not found at {args.script_path}")
        sys.exit(1)
        
    generate_podcast(args.script_path, args.out_dir, args.sub_dir)
