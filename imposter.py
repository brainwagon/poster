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
##


import sys
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

def drawRectangle(c, minx, miny, maxx, maxy):
    c.line(minx, miny, maxx, miny)
    c.line(minx, maxy, maxx, maxy)
    c.line(minx, miny, minx, maxy)
    c.line(maxx, miny, maxx, maxy)

def split_image_to_letter_overlap(image_path, output_pdf, poster_width=20, poster_height=30, dpi=300, overlap_in=0.5):

    # Hopelessly U.S. centric, no A sizes here...
    margin = 0.25
    letter_w, letter_h = 8.5-2.0*margin, 11.-2.0*margin

    overlap_px = int(overlap_in * dpi)
    poster_px_w = int(poster_width * dpi)
    poster_px_h = int(poster_height * dpi)
    sheet_px_w = int(letter_w * dpi)            # sheet_px_w is in pixels...
    sheet_px_h = int(letter_h * dpi)            # sheet_px_h is in pixels...

    im = Image.open(image_path)
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

    cols = (poster_px_w - overlap_px) // (sheet_px_w - overlap_px)
    rows = (poster_px_h - overlap_px) // (sheet_px_h - overlap_px)
    if (poster_px_w - overlap_px) % (sheet_px_w - overlap_px) != 0:
        cols += 1
    if (poster_px_h - overlap_px) % (sheet_px_h - overlap_px) != 0:
        rows += 1

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
            print(f"Image {col+1}x{row+1} has size {w}x{h}")

            # Draw segment on PDF page using drawInlineImage
            c.drawInlineImage(
                segment,
                margin*72, 
                (margin+overlap_in)*72 if row == rows-1 else margin*72,
                width=(letter_w * 72) * float(w) / sheet_px_w,  
                height=(letter_h * 72) * float(h) / sheet_px_h
            )

            # Draw prominent alignment lines
            c.setStrokeColor(Color(0, 0, 0, alpha=1.0))
            c.setLineWidth(1)
            c.setDash(1, 8)

            m = margin * 72

            if col > 0:
                x = overlap_in * 72
                c.line(x+m, 0+m, x+m, letter_h * 72+m)
            if col < cols - 1:
                x = (letter_w - overlap_in) * 72
                c.line(x+m, 0+m, x+m, letter_h * 72+m)

            if row > 0:
                y = (letter_h - overlap_in) * 72
                c.line(0+m, y+m, letter_w * 72+m, y+m)
            if row < rows - 1:
                y = overlap_in * 72
                c.line(0+m, y+m, letter_w * 72+m, y+m)



            # set a dashed box around the printable area...

            c.setDash(6, 3)
            drawRectangle(c, m, m, m+letter_w*72, m+letter_h*72)

            c.drawString(0, 0, f"image {row},{col}")

            # add the final cut marks for size... 
            c.setLineWidth(0.5)
            c.setDash(8,8)

            if col == cols-1:
                c.line(m+(letter_w * float(w) / sheet_px_w)*72, m,
                       m+(letter_w * float(w) / sheet_px_w)*72, m+letter_h * 72)

            if row == rows-1:
                x0 = m 
                x1 = m + letter_w * 72
                y0 = m + (1.0 - float(h) / sheet_px_h) * letter_h * 72
                y1 = y0

                c.line(x0, y0, x1, y1)

            c.showPage()

    c.save()
    print(f"PDF saved as: {output_pdf}")
    print(f"Sliced into {rows} rows and {cols} columns with {overlap_in}\" overlap.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python poster_split_no_distortion.py input_image output_pdf [dpi] [overlap_in]")
        sys.exit(1)
    image_path = sys.argv[1]
    output_pdf = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    overlap_in = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    split_image_to_letter_overlap(image_path, output_pdf, dpi=dpi, overlap_in=overlap_in)
