import re
import json
import argparse
import os

def normalize_hex(hex_str):
    """Normalizes hex string to 6 or 8 digits, uppercase, with # prefix."""
    hex_str = hex_str.lstrip('#').upper()
    
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    elif len(hex_str) == 4:
        hex_str = ''.join([c*2 for c in hex_str])
    
    if len(hex_str) not in [6, 8]:
        return None # Invalid hex
        
    return f"#{hex_str}"

def rgba_to_hex(r, g, b, a=None):
    """Converts RGB/RGBA to Hex."""
    r = int(r)
    g = int(g)
    b = int(b)
    
    if a is not None:
        try:
            alpha = float(a)
            if alpha > 1: # Maybe 0-255? CSS usually 0-1 for alpha in rgba()
                 # But sometimes people write 100%? Regex matches digits/dots.
                 if alpha <= 100: alpha = alpha / 100 # Assuming % if > 1? Unlikely in standard rgba(r,g,b, 0.5)
            alpha_int = int(alpha * 255)
            alpha_int = max(0, min(255, alpha_int))
            return f"#{r:02X}{g:02X}{b:02X}{alpha_int:02X}"
        except ValueError:
            pass
            
    return f"#{r:02X}{g:02X}{b:02X}"

def parse_swift_colors(swift_path):
    """Parses Swift file for color definitions."""
    color_map = {} # hex -> name
    
    if not os.path.exists(swift_path):
        print(f"Warning: Swift file not found at {swift_path}")
        return color_map

    with open(swift_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Regex 1: static let name = Color(hex: "#HEX")
    # Matches: static let brandPrimary = Color(hex: "#FF6B9D")
    simple_pattern = re.compile(r'static\s+let\s+(\w+)\s*=\s*Color\s*\(\s*hex:\s*"#?([0-9a-fA-F]+)"\s*\)')
    for match in simple_pattern.finditer(content):
        name = match.group(1)
        hex_val = normalize_hex(match.group(2))
        if hex_val:
            if hex_val not in color_map:
                color_map[hex_val] = name

    # Regex 2: dynamicColor(light: "#HEX", dark: "#HEX")
    # Matches: static let uiBackground = dynamicColor(light: "#F8FAFC", dark: "#121214")
    dynamic_pattern = re.compile(r'static\s+let\s+(\w+)\s*=\s*dynamicColor\s*\(\s*light:\s*"#?([0-9a-fA-F]+)"\s*,\s*dark:\s*"#?([0-9a-fA-F]+)"\s*\)')
    for match in dynamic_pattern.finditer(content):
        name = match.group(1)
        light_hex = normalize_hex(match.group(2))
        dark_hex = normalize_hex(match.group(3))
        
        if light_hex and light_hex not in color_map:
            color_map[light_hex] = name
        if dark_hex and dark_hex not in color_map:
            color_map[dark_hex] = name
            
    return color_map

def parse_html_colors(html_path):
    """Parses HTML file for color occurrences."""
    colors = set()
    
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return colors

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find Hex codes
    # Look for # followed by 3, 4, 6, or 8 hex chars, not followed by hex char.
    # We want to capture things that look like colors. 
    # Contexts: : #..., "#...", '#...
    hex_pattern = re.compile(r'#([0-9a-fA-F]{3,8})\b')
    for match in hex_pattern.finditer(content):
        norm = normalize_hex(match.group(1))
        if norm:
            colors.add(norm)
            
    # Find RGB/RGBA
    rgba_pattern = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([0-9.]+))?\s*\)')
    for match in rgba_pattern.finditer(content):
        r, g, b, a = match.groups()
        hex_val = rgba_to_hex(r, g, b, a)
        if hex_val:
            colors.add(hex_val)
            
    return list(colors)

def parse_tailwind_colors(html_content):
    """Parses Tailwind config JSON object for color definitions."""
    color_map = {} # hex -> name
    
    # Locate the tailwind.config object
    # This is a heuristic regex to find the colors object inside tailwind.config
    # It assumes a structure like: colors: { ... }
    
    # First, try to find the whole script block or config block
    config_match = re.search(r'tailwind\.config\s*=\s*(\{.*?\})\s*(?:;|</script>)', html_content, re.DOTALL)
    if not config_match:
        return color_map

    config_str = config_match.group(1)
    
    # Find the colors object. This is tricky with regex for nested braces, 
    # but usually colors is a direct property of theme.extend or theme.
    # We'll search for 'colors:\s*{' and grab until the next matching matching brace?
    # Simpler: just look for key-value pairs that look like colors inside the config string.
    
    # Regex for "key": "value" or key: "value" where value starts with #
    # We focus on lines that look like color definitions
    color_def_pattern = re.compile(r'["\']?([\w-]+)["\']?\s*:\s*["\'](#(?:[0-9a-fA-F]{3,8}))["\']')
    
    for match in color_def_pattern.finditer(config_str):
        name = match.group(1)
        hex_val = normalize_hex(match.group(2))
        
        if hex_val:
            # Convert kebab-case to camelCase for Swift compatibility
            if '-' in name:
                components = name.split('-')
                name = components[0] + ''.join(x.title() for x in components[1:])
            
            # Start with lowercase
            if name[0].isupper():
                name = name[0].lower() + name[1:]
                
            color_map[hex_val] = name
            
    return color_map

def main():
    parser = argparse.ArgumentParser(description="Extract colors from HTML and match with Swift.")
    parser.add_argument("--html-path", required=True, help="Path to HTML file")
    parser.add_argument("--swift-path", default="/Users/lizhi/WillsIdea/BrainTraining/AudioBook/BrainTraining/Utils/BTColor.swift", help="Path to Swift file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.html_path):
        print(f"Error: HTML file not found at {args.html_path}")
        return

    with open(args.html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    swift_map = parse_swift_colors(args.swift_path)
    tailwind_map = parse_tailwind_colors(html_content)
    
    # We pass the content directly to avoid reading it again, but parse_html_colors originally read file.
    # Let's refactor parse_html_colors to take content or just read it again (it's small).
    # Since I'm not editing parse_html_colors in this MultiReplace, I'll let it read the file again.
    found_colors = parse_html_colors(args.html_path) 
    
    results = {
        "colors": []
    }
    
    found_colors.sort() # Sort for consistency
    
    for hex_val in found_colors:
        entry = {
            "hex": hex_val,
        }
        
        # Priority 1: Existing Swift name
        if hex_val in swift_map:
            entry["name"] = swift_map[hex_val]
            entry["is_existing"] = True
            
        # Priority 2: Tailwind config name
        elif hex_val in tailwind_map:
            entry["name"] = tailwind_map[hex_val]
            entry["is_existing"] = False 
            entry["origin"] = "tailwind"

        # Priority 3: Check if it's an alpha variant of a known color (Swift or Tailwind)
        else:
            base_hex = hex_val[:7] # #RRGGBB
            alpha_hex = hex_val[7:] if len(hex_val) == 9 else ""
            
            matched_name = None
            if base_hex in swift_map:
                matched_name = swift_map[base_hex]
            elif base_hex in tailwind_map:
                matched_name = tailwind_map[base_hex]
                
            if matched_name and alpha_hex:
                # Calculate opacity percentage
                alpha_int = int(alpha_hex, 16)
                alpha_pct = int(round((alpha_int / 255.0) * 100))
                entry["name"] = f"{matched_name}{alpha_pct}"
                entry["is_existing"] = False
                entry["origin"] = "alpha_variant"
            else:
                entry["name"] = f"color_{hex_val.replace('#', '')}"
                entry["is_existing"] = False
            
        results["colors"].append(entry)
        
    # Output to JSON
    output_dir = os.path.dirname(args.html_path)
    filename = os.path.basename(args.html_path)
    output_filename = f"{os.path.splitext(filename)[0]}_colors.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    print(f"Successfully extracted {len(results['colors'])} colors.")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()
