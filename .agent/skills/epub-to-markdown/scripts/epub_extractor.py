import sys
import argparse
import zipfile
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from html.parser import HTMLParser

class EPUBToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        elif tag == "h1" or tag == "h2":
            self.output.append("\n# ")
        elif tag == "p":
            self.output.append("\n")

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
        elif tag == "h1" or tag == "h2":
            self.output.append("\n")
        elif tag == "p":
            self.output.append("\n")

    def handle_data(self, data):
        if self.in_body:
            self.output.append(data.strip())

    def get_text(self):
        return "".join(self.output).strip()

def get_opf_path(z):
    try:
        with z.open('META-INF/container.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            for rootfile in root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
                return rootfile.get('full-path')
    except Exception:
        pass
    return None

def extract_cover(z, opf_path, output_dir):
    if not opf_path: return False
    try:
        with z.open(opf_path) as f:
            content_str = f.read().decode('utf-8')
            
            cover_href = None
            m = re.search(r'<item[^>]+href="([^"]+)"[^>]+properties="cover-image"', content_str)
            if not m:
                m = re.search(r'<item[^>]+properties="cover-image"[^>]+href="([^"]+)"', content_str)
            if m:
                cover_href = m.group(1)
            
            if not cover_href:
                m = re.search(r'<meta[^>]+name="cover"[^>]+content="([^"]+)"', content_str)
                if m:
                    cover_id = m.group(1)
                    im = re.search(fr'<item[^>]+id="{cover_id}"[^>]+href="([^"]+)"', content_str)
                    if not im:
                        im = re.search(fr'<item[^>]+href="([^"]+)"[^>]+id="{cover_id}"', content_str)
                    if im:
                        cover_href = im.group(1)
                        
            if cover_href:
                cover_href = unquote(cover_href)
                opf_dir = os.path.dirname(opf_path)
                cover_full_path = f"{opf_dir}/{cover_href}" if opf_dir and cover_href and not cover_href.startswith('/') else cover_href
                cover_full_path = os.path.normpath(cover_full_path).replace('\\', '/')
                
                if cover_full_path in z.namelist():
                    ext = os.path.splitext(cover_full_path)[1]
                    cover_out_path = os.path.join(output_dir, f"cover{ext}")
                    with z.open(cover_full_path) as source, open(cover_out_path, "wb") as target:
                        target.write(source.read())
                    print(f"成功提取封面: {cover_out_path}")
                    return True
    except Exception as e:
        print(f"警告: 提取封面时出错: {e}")
    return False

def extract_chapters(epub_path, output_dir):
    with zipfile.ZipFile(epub_path, 'r') as z:
        opf_path = get_opf_path(z)
        opf_dir = os.path.dirname(opf_path) if opf_path else ""
        if opf_path:
            extract_cover(z, opf_path, output_dir)
            
        # Try to find TOC in OPF
        toc_href = None
        if opf_path:
            with z.open(opf_path) as f:
                content_str = f.read().decode('utf-8')
                # Try finding NCX in spine
                m = re.search(r'<spine[^>]+toc="([^"]+)"', content_str)
                if m:
                    toc_id = m.group(1)
                    # Find item with this ID
                    im = re.search(fr'<item[^>]+id="{toc_id}"[^>]+href="([^"]+)"', content_str)
                    if im:
                        toc_href = im.group(1)

        # Fallback paths
        possible_tocs = []
        if toc_href:
            possible_tocs.append(os.path.join(opf_dir, toc_href).replace('\\', '/').lstrip('/'))
        possible_tocs.extend([
            "EPUB/nav.xhtml",
            "nav.xhtml",
            "toc.ncx",
            "OEBPS/toc.ncx",
            "OEBPS/nav.xhtml"
        ])
        
        found_toc = None
        for path in possible_tocs:
            if path in z.namelist():
                found_toc = path
                break
        
        if not found_toc:
            print("Error: Table of Contents (nav.xhtml or toc.ncx) not found.")
            return

        print(f"Using TOC: {found_toc}")
        with z.open(found_toc) as f:
            toc_content = f.read().decode('utf-8', errors='ignore')

        matches = []
        toc_base_dir = os.path.dirname(found_toc)

        if found_toc.endswith('.ncx'):
            # Parse NCX
            # <navPoint ...><navLabel><text>Title</text></navLabel><content src="path/to/file.xhtml"/></navPoint>
            # Use a simpler regex for NCX
            pattern = re.compile(r'<navPoint[^>]*>.*?<text>([^<]+)</text>.*?<content src="([^"]+)"', re.DOTALL)
            matches = [(href, title) for title, href in pattern.findall(toc_content)]
        else:
            # Parse nav.xhtml (HTML5)
            pattern = re.compile(r'<li>\s*<a href="([^"]+)">([^<]+)</a>\s*</li>', re.DOTALL)
            matches = pattern.findall(toc_content)

        if not matches:
            print("No chapters found in TOC.")
            return

        for href, title in matches:
            # Remove anchors from href
            clean_href = href.split('#')[0]
            # Format filename
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).strip()
            if not safe_title: continue
            filename = f"{safe_title}.md"
            filepath = os.path.join(output_dir, filename)

            # Resolve internal path relative to TOC location
            internal_path = os.path.join(toc_base_dir, clean_href).replace('\\', '/').lstrip('/')
            
            # If still not found, try relative to OPF dir
            if internal_path not in z.namelist() and opf_dir:
                internal_path = os.path.join(opf_dir, clean_href).replace('\\', '/').lstrip('/')

            if internal_path in z.namelist():
                print(f"Extracting {title}...")
                with z.open(internal_path) as f_ch:
                    html_content = f_ch.read().decode('utf-8', errors='ignore')
                    
                    # Convert to text/markdown
                    parser = EPUBToMarkdown()
                    parser.feed(html_content)
                    markdown_content = parser.get_text()

                    with open(filepath, 'w', encoding='utf-8') as f_out:
                        f_out.write(f"# {title}\n\n")
                        f_out.write(markdown_content)
            else:
                print(f"Warning: {internal_path} not found in zip.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取 EPUB 为 markdown 章节。")
    parser.add_argument("epub_path", help="要提取的 EPUB 文件路径")
    parser.add_argument("--output_base", default="chapters", help="保存章节的基础文件夹名（默认：chapters）")
    args = parser.parse_args()

    if not os.path.exists(args.epub_path):
        print(f"错误: 找不到 EPUB 文件 '{args.epub_path}'")
        sys.exit(1)

    # 以 EPUB 文件名（不含后缀）作为章节存放的子目录名
    epub_filename = os.path.basename(args.epub_path)
    epub_name = os.path.splitext(epub_filename)[0]
    
    # 最终输出路径为 chapters/书名
    output_dir = os.path.join(args.output_base, epub_name)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"正在提取: {args.epub_path}")
    print(f"输出目录: {output_dir}")
    extract_chapters(args.epub_path, output_dir)
