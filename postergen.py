#!/usr/bin/env python3
"""
Text to Image Generator

A script that converts text files to images with automatically sized text,
proper centering, and configurable spacing.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import platform


def get_system_fonts():
    """Get available system fonts based on the operating system."""
    system = platform.system().lower()
    font_paths = []
    
    if system == "windows":
        font_dirs = [
            "C:/Windows/Fonts/",
            "C:/Windows/System32/Fonts/"
        ]
    elif system == "darwin":  # macOS
        font_dirs = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            "~/Library/Fonts/"
        ]
    else:  # Linux and others
        font_dirs = [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            "~/.fonts/",
            "~/.local/share/fonts/"
        ]
    
    # Expand user paths and collect font files
    for font_dir in font_dirs:
        font_path = Path(font_dir).expanduser()
        if font_path.exists():
            for ext in ['*.ttf', '*.otf', '*.TTF', '*.OTF']:
                font_paths.extend(font_path.glob(f"**/{ext}"))
    
    # Sort and return unique font names
    font_names = sorted(set(fp.stem for fp in font_paths))
    return font_names, font_paths


def find_font_path(font_name, font_paths):
    """Find the full path for a given font name."""
    font_name_lower = font_name.lower().replace(' ', '').replace('-', '')
    
    for font_path in font_paths:
        # Try exact match first
        if font_path.stem.lower() == font_name.lower():
            return str(font_path)
        
        # Try match without spaces and hyphens
        path_name = font_path.stem.lower().replace(' ', '').replace('-', '')
        if path_name == font_name_lower:
            return str(font_path)
        
        # Try partial match (font name contained in filename)
        if font_name_lower in path_name:
            return str(font_path)
    
    return None


def parse_line_formatting(line):
    """Parse line for formatting directives and return processed line, alignment, and size modifier."""
    if not line:
        return line, 'center', 1.0, False
    
    first_char = line[0]
    
    # Check for alignment modifiers
    if first_char == '<':
        return line[1:], 'left', 1.0, False
    elif first_char == '>':
        return line[1:], 'right', 1.0, False
    # Check for size modifiers
    elif first_char == '-':
        return line[1:], 'center', 0.75, False  # 25% smaller
    elif first_char == '+':
        return line[1:], 'center', 1.5, False   # 50% bigger
    # Check for full-width formatting
    elif first_char == '=':
        return line[1:], 'center', 1.0, True    # Fill width
    else:
        return line, 'center', 1.0, False


def calculate_fill_width_font_size(text, available_width, font_path):
    """Calculate font size to make text fill the available width exactly."""
    if not font_path or not text.strip():
        return 20
    
    # Binary search for the largest font size that fills the width
    min_size, max_size = 1, 500
    best_size = 1
    
    while min_size <= max_size:
        font_size = (min_size + max_size) // 2
        
        try:
            font = ImageFont.truetype(font_path, font_size)
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            
            if text_width <= available_width:
                best_size = font_size
                min_size = font_size + 1
            else:
                max_size = font_size - 1
                
        except (OSError, IOError):
            max_size = font_size - 1
    
    return best_size


def calculate_base_font_size(non_fullwidth_lines, width, height, font_path, line_spacing_ratio, margin_x, margin_y):
    """Calculate font size for non-full-width lines only."""
    if not non_fullwidth_lines:
        return 20
        
    available_width = width - (2 * margin_x)
    available_height = height - (2 * margin_y)
    
    # Binary search for optimal base font size
    min_size, max_size = 1, 200
    best_size = 1
    
    while min_size <= max_size:
        font_size = (min_size + max_size) // 2
        
        try:
            base_font = ImageFont.truetype(font_path, font_size)
        except (OSError, IOError):
            max_size = font_size - 1
            continue
        
        # Calculate total height and max width for non-full-width lines
        total_height = 0
        max_width = 0
        base_line_height = base_font.getbbox("AgjpqyQ|")[3] - base_font.getbbox("AgjpqyQ|")[1]
        
        fits = True
        for i, line_data in enumerate(non_fullwidth_lines):
            if line_data['is_empty']:
                total_height += base_line_height * 0.25
            else:
                actual_font_size = int(font_size * line_data['size_modifier'])
                try:
                    line_font = ImageFont.truetype(font_path, actual_font_size)
                except (OSError, IOError):
                    fits = False
                    break
                    
                line_height = line_font.getbbox("AgjpqyQ|")[3] - line_font.getbbox("AgjpqyQ|")[1]
                total_height += line_height
                
                # Add spacing between non-empty lines
                if i < len(non_fullwidth_lines) - 1 and not non_fullwidth_lines[i + 1]['is_empty']:
                    total_height += line_height * line_spacing_ratio
                
                # Check width
                if line_data['text'].strip():
                    text_bbox = line_font.getbbox(line_data['text'])
                    text_width = text_bbox[2] - text_bbox[0]
                    max_width = max(max_width, text_width)
        
        if fits and total_height <= available_height and max_width <= available_width:
            best_size = font_size
            min_size = font_size + 1
        else:
            max_size = font_size - 1
    
    return best_size


def create_text_image(text_file, output_file, width, height, font_name=None, 
                     line_spacing_ratio=0.12, margin_x_ratio=0.05, margin_y_ratio=0.05,
                     bg_color=(255, 255, 255), text_color=(0, 0, 0)):
    """Create an image from text file with specified parameters."""
    
    # Read text file and parse formatting
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            raw_lines = [line.rstrip() for line in f.readlines()]
        
        # Parse each line for formatting directives, including empty lines
        lines_data = []
        for line in raw_lines:
            if line:  # Non-empty line
                text, alignment, size_modifier, fill_width = parse_line_formatting(line)
                if text:  # Only add if there's text after removing formatting chars
                    lines_data.append({
                        'text': text,
                        'alignment': alignment,
                        'size_modifier': size_modifier,
                        'fill_width': fill_width,
                        'is_empty': False
                    })
            else:  # Empty line - add as spacing
                lines_data.append({
                    'text': '',
                    'alignment': 'center',
                    'size_modifier': 1.0,
                    'fill_width': False,
                    'is_empty': True
                })
        
        if not lines_data:
            print("Error: No content found in file.")
            return False
            
    except FileNotFoundError:
        print(f"Error: File '{text_file}' not found.")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

    # Calculate margins
    margin_x = int(width * margin_x_ratio)
    margin_y = int(height * margin_y_ratio)
    available_width = width - (2 * margin_x)
    
    # Get font path
    font_names, font_paths = get_system_fonts()
    font_path = None
    
    if font_name:
        font_path = find_font_path(font_name, font_paths)
        if not font_path:
            print(f"Warning: Font '{font_name}' not found.")
    
    # If no font specified or font not found, try to use a common system font
    if not font_path:
        # Common fonts to try, in order of preference
        common_fonts = ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans', 
                       'Ubuntu', 'Roboto', 'Times New Roman', 'Georgia']
        
        for common_font in common_fonts:
            font_path = find_font_path(common_font, font_paths)
            if font_path:
                print(f"Using system font: {common_font}")
                break
        
        if not font_path:
            print("Warning: No suitable system fonts found. Text may be small.")
            print("Try using -l to list available fonts and specify one with -f")

    # Separate full-width lines from regular lines for font sizing
    non_fullwidth_lines = [line for line in lines_data if not line['fill_width']]
    
    # Calculate base font size for non-full-width lines
    if font_path and non_fullwidth_lines:
        base_font_size = calculate_base_font_size(
            non_fullwidth_lines, width, height, font_path, line_spacing_ratio, margin_x, margin_y
        )
        print(f"Using base font size: {base_font_size}")
    else:
        base_font_size = 11
        print("Using default font (fixed size, cannot be optimized)")

    # Create image and calculate line info
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Pre-calculate all fonts and line heights
    line_info = []
    total_height = 0
    
    for line_data in lines_data:
        if line_data['is_empty']:
            # Empty line spacing
            if font_path:
                try:
                    base_font = ImageFont.truetype(font_path, base_font_size)
                    base_line_height = base_font.getbbox("AgjpqyQ|")[3] - base_font.getbbox("AgjpqyQ|")[1]
                except:
                    base_line_height = 20
            else:
                base_line_height = 20
            
            empty_height = base_line_height * 0.25
            line_info.append({
                'height': empty_height,
                'font': None,
                'is_empty': True
            })
            total_height += empty_height
            
        elif line_data['fill_width']:
            # Full-width line - calculate independent font size
            if font_path:
                fill_font_size = calculate_fill_width_font_size(
                    line_data['text'], available_width, font_path
                )
                try:
                    fill_font = ImageFont.truetype(font_path, fill_font_size)
                    print(f"Full-width line '{line_data['text']}' using font size: {fill_font_size}")
                except:
                    fill_font = ImageFont.load_default()
            else:
                fill_font = ImageFont.load_default()
            
            line_height = fill_font.getbbox("AgjpqyQ|")[3] - fill_font.getbbox("AgjpqyQ|")[1]
            line_info.append({
                'height': line_height,
                'font': fill_font,
                'is_empty': False
            })
            total_height += line_height
            
        else:
            # Regular line with base font size and modifiers
            actual_font_size = int(base_font_size * line_data['size_modifier'])
            
            if font_path:
                try:
                    line_font = ImageFont.truetype(font_path, actual_font_size)
                except:
                    line_font = ImageFont.load_default()
            else:
                line_font = ImageFont.load_default()
            
            line_height = line_font.getbbox("AgjpqyQ|")[3] - line_font.getbbox("AgjpqyQ|")[1]
            line_info.append({
                'height': line_height,
                'font': line_font,
                'is_empty': False
            })
            total_height += line_height
    
    # Add spacing between consecutive text lines
    spacing_total = 0
    for i in range(len(lines_data) - 1):
        if not lines_data[i]['is_empty'] and not lines_data[i + 1]['is_empty']:
            spacing = line_info[i]['height'] * line_spacing_ratio
            spacing_total += spacing
    
    total_height += spacing_total
    
    # Start drawing from center
    current_y = (height - total_height) // 2
    
    # Draw all lines
    for i, line_data in enumerate(lines_data):
        if line_data['is_empty']:
            current_y += line_info[i]['height']
        else:
            font = line_info[i]['font']
            
            # Calculate text width for alignment
            text_bbox = font.getbbox(line_data['text'])
            text_width = text_bbox[2] - text_bbox[0]
            
            # Determine X position based on alignment
            if line_data['alignment'] == 'left':
                x = margin_x
            elif line_data['alignment'] == 'right':
                x = width - margin_x - text_width
            else:  # center
                x = (width - text_width) // 2
            
            # Draw the text
            draw.text((x, current_y), line_data['text'], fill=text_color, font=font)
            current_y += line_info[i]['height']
            
            # Add spacing if next line is also text
            if i < len(lines_data) - 1 and not lines_data[i + 1]['is_empty']:
                current_y += int(line_info[i]['height'] * line_spacing_ratio)

    # Save image
    try:
        image.save(output_file)
        print(f"Image saved successfully as '{output_file}'")
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def list_fonts():
    """List all available system fonts."""
    print("Available fonts:")
    print("-" * 50)
    
    font_names, _ = get_system_fonts()
    
    if not font_names:
        print("No system fonts found.")
        return
    
    for i, font_name in enumerate(font_names, 1):
        print(f"{i:3d}. {font_name}")
    
    print(f"\nTotal fonts found: {len(font_names)}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate an image from a text file with automatically sized text."
    )
    
    parser.add_argument(
        "text_file", 
        nargs="?",
        help="Input text file path"
    )
    
    parser.add_argument(
        "output_file",
        nargs="?", 
        help="Output image file path"
    )
    
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=800,
        help="Image width in pixels (default: 800)"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=600,
        help="Image height in pixels (default: 600)"
    )
    
    parser.add_argument(
        "-f", "--font",
        help="Font name to use (use -l to list available fonts)"
    )
    
    parser.add_argument(
        "-s", "--line-spacing",
        type=float,
        default=0.12,
        help="Line spacing as ratio of font height (default: 0.12)"
    )
    
    parser.add_argument(
        "-mx", "--margin-x",
        type=float,
        default=0.05,
        help="Horizontal margin as ratio of image width (default: 0.05)"
    )
    
    parser.add_argument(
        "-my", "--margin-y",
        type=float,
        default=0.05,
        help="Vertical margin as ratio of image height (default: 0.05)"
    )
    
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available fonts and exit"
    )
    
    parser.add_argument(
        "--bg-color",
        default="white",
        help="Background color (default: white)"
    )
    
    parser.add_argument(
        "--text-color",
        default="black",
        help="Text color (default: black)"
    )
    
    args = parser.parse_args()
    
    # If --list is specified, show fonts and exit
    if args.list:
        list_fonts()
        return
    
    # Check required arguments
    if not args.text_file or not args.output_file:
        print("Error: Both text_file and output_file are required (unless using -l/--list)")
        parser.print_help()
        sys.exit(1)
    
    # Parse colors (simple color names or RGB tuples)
    def parse_color(color_str):
        color_map = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
        }
        return color_map.get(color_str.lower(), (255, 255, 255))
    
    bg_color = parse_color(args.bg_color)
    text_color = parse_color(args.text_color)
    
    # Create the image
    success = create_text_image(
        args.text_file,
        args.output_file,
        args.width,
        args.height,
        args.font,
        args.line_spacing,
        args.margin_x,
        args.margin_y,
        bg_color,
        text_color
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
