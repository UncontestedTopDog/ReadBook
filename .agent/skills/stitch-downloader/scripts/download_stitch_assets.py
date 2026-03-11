import os
import sys
import argparse
import urllib.request
import re

def sanitize_filename(name):
    # Remove invalid characters for filenames
    # Keep spaces, alphanumeric, dashes, underscores, dots
    # Remove slashes, colons, etc.
    s = re.sub(r'[<>:"/\\|?*]', '', name)
    return s.strip()

def get_unique_filename(base_name, ext, directory):
    counter = 0
    while True:
        suffix = "" if counter == 0 else f" {counter}"
        filename = f"{base_name}{suffix}{ext}"
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1

import subprocess

def download_file(url, filepath):
    try:
        print(f"Downloading to {filepath}...")
        # Use curl via subprocess to avoid python SSL certificate issues on some environments
        result = subprocess.run(
            ["curl", "-L", "-o", filepath, url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Successfully downloaded: {filepath}")
            return True
        else:
            print(f"Error downloading {filepath}: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error executing curl for {filepath}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download Stitch assets with unique naming.")
    parser.add_argument("--title", required=True, help="Title of the design")
    parser.add_argument("--png-url", required=True, help="URL for the screenshot")
    parser.add_argument("--html-url", required=True, help="URL for the HTML code")
    parser.add_argument("--output-dir", default="stitch_downloads", help="Directory to save files")

    args = parser.parse_args()

    title = args.title
    png_url = args.png_url
    html_url = args.html_url
    output_dir = args.output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    safe_title = sanitize_filename(title)
    
    # Determine unique base name for both (to keep them matching if possible)
    # Actually, we should probably check uniqueness for them individually or as a pair?
    # Usually we want "Title.png" and "Title.html".
    # If "Title.png" exists, we want "Title 1.png" and "Title 1.html".
    
    counter = 0
    while True:
        suffix = "" if counter == 0 else f" {counter}"
        base_filename = f"{safe_title}{suffix}"
        
        png_path = os.path.join(output_dir, f"{base_filename}.png")
        html_path = os.path.join(output_dir, f"{base_filename}.html")
        
        if not os.path.exists(png_path) and not os.path.exists(html_path):
            break
        counter += 1

    # Now download
    download_file(png_url, png_path)
    download_file(html_url, html_path)

if __name__ == "__main__":
    main()
