#!/usr/bin/env python 

##   _                    _           
##  (_)_ __  _ __  ___ __| |_ ___ _ _ 
##  | | '  \| '_ \/ _ (_-<  _/ -_) '_|
##  |_|_|_|_| .__/\___/__/\__\___|_|  
##          |_|                       
##       
## my own simplified version of the "poster" program that you can get on linux.  I've had a 
## bunch of problems debugging the exact size of printouts, which actually can be laid at the 
## feet of bad printer drivers, but I figured I should continue to develop this to make it
## obvious.
## 
## Written by Mark VandeWettering, with some help from ChatGPT 4.1
## Generalized by Claude to accept custom poster sizes
##

import sys
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib import colors
import argparse
import math

def drawRectangle(c, minx, miny, maxx, maxy):
    c.line(minx, miny, maxx, miny)
    c.line(minx, maxy, maxx, maxy)
    c.line(minx, miny, minx, maxy)
    c.line(maxx, miny, maxx, maxy)

def parse_size(size_str):
    """Parse size string like '20x30' or '24x36' into width, height tuple"""
    try:
        parts = size_str.lower().split('x')
        if len(parts) != 2:
            raise ValueError("Size must be in format WIDTHxHEIGHT")
        width = float(parts[0])
        height = float(parts[1])
        return width, height
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid size format '{size_str}'. Use format like '20x30' or '24.5x36'") from e

def parse_margin(margin_str):
    """Parse margin string like '0.5,0.25' or '0.5' into a tuple"""
    try:
        parts = margin_str.split(',')
        if len(parts) == 1:
            margin = float(parts[0])
            return margin, margin
        elif len(parts) == 2:
            margin_x = float(parts[0])
            margin_y = float(parts[1])
            return margin_x, margin_y
        else:
            raise ValueError("Margin must be in format 'x,y' or a single value")
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid margin format '{margin_str}'. Use format like '0.5,0.25' or '0.5'") from e

def calculate_pages_needed(poster_width, poster_height, dpi=300, overlap_in=0.5, margin_x=0.25, margin_y=0.25):
    """Calculate how many letter-sized pages are needed for the given poster size"""
    # Printable area on letter paper (8.5" x 11" minus margins)
    letter_w = 8.5 - 2.0 * margin_x
    letter_h = 11.0 - 2.0 * margin_y
    
    # Convert to pixels
    overlap_px = int(overlap_in * dpi)
    poster_px_w = int(poster_width * dpi)
    poster_px_h = int(poster_height * dpi)
    sheet_px_w = int(letter_w * dpi)
    sheet_px_h = int(letter_h * dpi)
    
    # Calculate number of columns and rows needed
    cols = math.ceil((poster_px_w - overlap_px) / (sheet_px_w - overlap_px))
    rows = math.ceil((poster_px_h - overlap_px) / (sheet_px_h - overlap_px))
    
    return cols, rows

def parse_color(color_str):
    """Parse color string (e.g., 'red', '#RRGGBB') into a reportlab Color object."""
    if color_str.startswith('#'):
        # Hex color
        hex_color = color_str[1:]
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return Color(r, g, b)
        else:
            raise ValueError(f"Invalid hex color format: {color_str}. Use #RRGGBB.")
    else:
        # Named color
        if hasattr(colors, color_str.lower()):
            return getattr(colors, color_str.lower())
        else:
            raise ValueError(f"Unknown color name: {color_str}")

def split_image_to_letter_overlap(image_path, output_pdf, poster_width=20, poster_height=30, dpi=300, overlap_in=0.5,
        args=None, rotated=False, line_color_str="black", margin_x=0.375, margin_y=0.375):

    # Hopelessly U.S. centric, no A sizes here...
    letter_w, letter_h = 8.5-2.0*margin_x, 11.-2.0*margin_y

    overlap_px = int(overlap_in * dpi)
    poster_px_w = int(poster_width * dpi)
    poster_px_h = int(poster_height * dpi)
    sheet_px_w = int(letter_w * dpi)            # sheet_px_w is in pixels...
    sheet_px_h = int(letter_h * dpi)            # sheet_px_h is in pixels...

    print(f"Poster size: {poster_width}\" x {poster_height}\"")
    print(f"DPI: {dpi}")
    print(f"Overlap: {overlap_in}\"")
    print(f"Black and white: {args.black_and_white if args else False}")
    print(f"Line color: {line_color_str}")

    try:
        line_color = parse_color(line_color_str)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    im = Image.open(image_path)
    if rotated:
        im = im.rotate(90, expand=True)

    if args and args.black_and_white:
        im = im.convert('L')
        im = im.point(lambda p : 0 if p < 128 else 255)
        im = im.convert('1')
        print("... converted to black and white")
    else:
        im = im.convert('RGB')
    iw, ih = im.size

    # If the input matches the target ratio, scale it up or down to match poster size
    target_ratio = poster_px_w / poster_px_h
    input_ratio = iw / ih
    if abs(target_ratio - input_ratio) > 1e-4:
        print(f"Warning: input aspect ratio {input_ratio:.4f} != target {target_ratio:.4f}")

    print(f"Resizing image to {poster_px_w}x{poster_px_h}...", end="")

    if iw != poster_px_w or ih != poster_px_h:
        im = im.resize((poster_px_w, poster_px_h), Image.NEAREST)
    print("done.")

    # Calculate pages needed
    cols, rows = calculate_pages_needed(poster_width, poster_height, dpi, overlap_in, margin_x, margin_y)
    
    print(f"Will need {cols} columns x {rows} rows = {cols * rows} total pages")

    c = canvas.Canvas(output_pdf, pagesize=letter)

    for row in range(rows):
        for col in range(cols):
            left = col * (sheet_px_w - overlap_px)
            upper = row * (sheet_px_h - overlap_px)
            right = min(left + sheet_px_w, poster_px_w)
            lower = min(upper + sheet_px_h, poster_px_h)
            box = (left, upper, right, lower)
            segment = im.crop(box)

            # crop the image... I believe that his can return 
            # an image which is smaller than that specified by "box"

            w, h = segment.size
            print(f"Page {row * cols + col + 1:2d}: Image segment {col+1}x{row+1} has size {w}x{h}")

            print(f"height = {h}")
            # sheet_px_h = sheet_height in pixels
            # h is the height in pixels 
            offset = (float(sheet_px_h - h) / sheet_px_h) * letter_h
            print(f"offset = {offset} inches")
            print(f"letter_h = {letter_h}")

            # Draw segment on PDF page using drawInlineImage
            c.drawInlineImage(
                segment,
                margin_x*72, 
                (margin_y+offset)*72 if row == rows-1 else margin_y * 72,
                width=(letter_w * 72) * float(w) / sheet_px_w,  
                height=(letter_h * 72) * float(h) / sheet_px_h
            )

            # Draw prominent alignment lines
            c.setStrokeColor(line_color)
            c.setLineWidth(1)
            c.setDash(1, 8)

            m_x = margin_x * 72
            m_y = margin_y * 72

            minx = m_x
            maxx = m_x + (letter_w * float(w) / sheet_px_w) * 72

            miny = m_y
            maxy = m_y + (letter_h * float(h) / sheet_px_h) * 72
            if row == rows - 1:
                miny = m_y + offset * 72
                maxy = m_y + offset * 72 + (letter_h * float(h) / sheet_px_h) * 72

            if col > 0:
                x = overlap_in * 72
                c.line(x+m_x, miny, x+m_x, maxy)
            if col < cols - 1:
                x = (letter_w - overlap_in) * 72
                c.line(x+m_x, miny, x+m_x, maxy)

            if row > 0:
                y = (letter_h - overlap_in) * 72
                c.line(minx, y+m_y, maxx, y+m_y)
            if row < rows - 1:
                y = overlap_in * 72
                c.line(minx, y+m_y, maxx, y+m_y)

            # set a dashed box around the image area...
            c.setDash(6, 3)
            
            maxx = m_x + letter_w * 72
            if col == cols - 1:
                maxx = m_x + (letter_w * float(w) / sheet_px_w) * 72

            miny = m_y
            maxy = m_y + letter_h * 72
            if row == rows - 1:
                # for the last row, the image is aligned to the top of the
                # page.  The offset calculation determines the amount of blank
                # space at the bottom of the page.
                miny = m_y + offset * 72
            
            drawRectangle(c, m_x, miny, maxx, maxy)

            c.drawString(10, 10, f"Page {row * cols + col + 1} (row {row+1}, col {col+1})")



            c.showPage()

    c.save()
    print(f"PDF saved as: {output_pdf}")
    print(f"Sliced into {rows} rows and {cols} columns with {overlap_in}\" overlap.")
    print(f"Total pages: {rows * cols}")

def main():
    p = argparse.ArgumentParser(
        description="Split an image into multiple letter-sized pages for poster printing",
        epilog="Example: python imposter.py -s 24x36 --dpi 300 --overlap 0.5 image.jpg poster.pdf"
    )
    p.add_argument("-s", "--size", default="20x30", 
                   help="Poster size in inches as WIDTHxHEIGHT (default: 20x30)")
    p.add_argument("-b", "--black-and-white", action="store_true", 
                   help="Convert the image to black and white")
    p.add_argument("--dpi", default=300, type=int,
                   help="Dots per inch resolution (default: 300)")
    p.add_argument("--overlap", default=0.25, type=float,
                   help="Overlap between pages in inches (default: 0.125)")
    p.add_argument("--margin", default="0.5", type=str,
                   help="Margin for all pages in inches (default: 0.375). Can be a single value or in 'x,y' format.")
    p.add_argument("--line-color", default="black", type=str,
                     help="Color of the overlap lines (default: black)")
    p.add_argument("--preview", action="store_true",
                   help="Show how many pages will be needed without processing")
    p.add_argument("--no-rotate", action="store_true",
                     help="Disable automatic rotation of the image for fewer pages")
    p.add_argument("image", help="Input image file name")
    p.add_argument("output", help="Output PDF file name")
    
    args = p.parse_args()
    
    try:
        poster_width, poster_height = parse_size(args.size)
        margin_x, margin_y = parse_margin(args.margin)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    rotated = False
    if not args.no_rotate:
        cols, rows = calculate_pages_needed(poster_width, poster_height, args.dpi, args.overlap, margin_x, margin_y)
        rotated_cols, rotated_rows = calculate_pages_needed(poster_height, poster_width, args.dpi, args.overlap, margin_y, margin_x)

        if rotated_cols * rotated_rows < cols * rows:
            print("Rotating image to save pages")
            poster_width, poster_height = poster_height, poster_width
            rotated = True

    # Preview mode - just show page count
    if args.preview:
        cols, rows = calculate_pages_needed(poster_width, poster_height, args.dpi, args.overlap, margin_x, margin_y)
        print(f"Poster size: {poster_width}\" x {poster_height}\"")
        print(f"Pages needed: {cols} columns x {rows} rows = {cols * rows} total pages")
        print(f"With {args.dpi} DPI and {args.overlap}\" overlap")
        return
    
    split_image_to_letter_overlap(
        args.image, 
        args.output, 
        poster_width=poster_width,
        poster_height=poster_height,
        dpi=args.dpi, 
        overlap_in=args.overlap, 
        args=args,
        rotated=rotated,
        line_color_str=args.line_color,
        margin_x=margin_x,
        margin_y=margin_y
    )

if __name__ == '__main__':
    main()
